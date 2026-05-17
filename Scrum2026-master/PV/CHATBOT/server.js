// server.js

import express from "express";
import cors from "cors";
import fs from "fs";
import path from "path";
import { parse } from "csv-parse/sync";
import { LMStudioClient } from "@lmstudio/sdk";
import stringSimilarity from "string-similarity";

// ================= SYSTEM PROMPT =================
const SYSTEM_PROMPT = `
Sei un assistente post vendita del Morato Group e non devi riportare il cliente a contattare il servizio post-vendita. Non devi mai portare al servizio-clienti.

REGOLE FERREE:
- Ogni richiesta è INDIPENDENTE
- Usa il CSV come base dati principale
- Se trovi una risposta nel CSV, riformulala in modo preciso
- Se non trovi nulla nel CSV, usa conoscenza generale SOLO sui panificati
- Non inventare numeri, email, contatti, procedure
- Non parlare di prodotti non menzionati
- Risposte brevi, pratiche, sicure (1-2 frasi)
- Niente frasi emotive inutili
- Non spiegare come si produce il pane
- Tu sei la sezione clienti, non rimandare mai ad essa
- Non portare mai il discorso su altri reparti
- Tu sei la post vendita e quindi non devi MAI portare il cliente a contattare il servizio post-vendita
`;

// ================= UTILS =================
function normalize(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

// ================= FILE ISSUES =================
const ISSUES_FILE = "./frequent_issues.json";

function loadIssues() {
  try {
    if (!fs.existsSync(ISSUES_FILE)) {
      fs.writeFileSync(ISSUES_FILE, "{}");
      return {};
    }

    const raw = fs.readFileSync(ISSUES_FILE, "utf-8").trim();
    if (!raw) return {};

    return JSON.parse(raw);
  } catch (err) {
    console.error("⚠️ frequent_issues.json corrotto, reset automatico");
    fs.writeFileSync(ISSUES_FILE, "{}");
    return {};
  }
}

// ================= ESTRAZIONE KEYWORDS AI =================
async function extractKeywordsAI(text, model) {
  const prompt = `
Estrai 1-2 parole chiave significative dalla seguente frase. Non aggiungere altro.
Frase: "${text}"
Rispondi solo con le parole chiave separate da uno spazio.
`;

  try {
    const result = await model.respond(
      [
        { role: "system", content: "Sei un estrattore di parole chiave." },
        { role: "user", content: prompt }
      ],
      { max_tokens: 10, temperature: 0 }
    );

    return result.content?.trim().toLowerCase().replace(/[^\w\s]/g, "") || "altro";
  } catch (err) {
    console.error("Errore extractKeywordsAI:", err);
    return "altro";
  }
}

// ================= SALVATAGGIO STATISTICHE =================
async function saveIssueFromText(text, covered, model) {
  const issues = loadIssues();
  const key = await extractKeywordsAI(text, model);

  if (!issues[key]) {
    issues[key] = {
      count: 0,
      covered_count: 0,
      uncovered_count: 0,
      examples: []
    };
  }

  issues[key].count += 1;
  covered ? issues[key].covered_count++ : issues[key].uncovered_count++;

  if (issues[key].examples.length < 5) {
    issues[key].examples.push(text);
  }

  fs.writeFileSync(ISSUES_FILE, JSON.stringify(issues, null, 2));
}

// ================= SERVER =================
async function main() {
  const app = express();
  app.use(cors());
  app.use(express.json());
  app.use(express.static(path.resolve("./")));

  app.get("/", (req, res) => {
    res.sendFile(path.resolve("./index.html"));
  });

  // ===== CSV LOAD =====
  const csvFile = fs.readFileSync("./dataset.csv");
  const records = parse(csvFile, {
    columns: true,
    skip_empty_lines: true
  });

  function findCSVMatch(question) {
    const q = normalize(question);
    const questions = records.map(r => normalize(r.question));

    const matches = stringSimilarity.findBestMatch(q, questions);
    const best = matches.ratings
      .map((r, i) => ({ index: i, score: r.rating }))
      .sort((a, b) => b.score - a.score)[0];

    return best && best.score >= 0.6 ? records[best.index] : null;
  }

  // ===== LM STUDIO =====
  const client = new LMStudioClient();
  const model = await client.llm.model("llama-3.2-3b-instruct");

  // ===== API: ASK =====
  app.post("/ask", async (req, res) => {
    try {
      const question = req.body.question?.trim();
      if (!question) return res.json({ answer: "" });

      const csvMatch = findCSVMatch(question);

      // 🔥 SALVATAGGIO STATISTICHE
      if (csvMatch) {
        await saveIssueFromText(csvMatch.question, true, model);
      } else {
        await saveIssueFromText(question, false, model);
      }

      let userPrompt = `
Domanda utente:
${question}
`;

      if (csvMatch) {
        userPrompt += `
Informazione dal CSV:
${csvMatch.question} → ${csvMatch.answer}

Riformula la risposta in modo preciso per la domanda.
`;
      } else {
        userPrompt += `
Non ci sono risposte dirette nel CSV.
Fornisci una risposta pratica e sicura limitata ai panificati.
`;
      }

      const result = await model.respond(
        [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: userPrompt }
        ],
        {
          max_tokens: 80,
          temperature: 0.3
        }
      );

      const answer =
        result.content?.trim() ||
        "Posso fornire informazioni solo su prodotti da forno.";

      res.json({ answer });
    } catch (err) {
      console.error("Errore /ask:", err);
      res.json({ answer: "Errore nella risposta." });
    }
  });

  // ===== EXPORT CSV =====
  app.get("/export-frequent-issues", (req, res) => {
    const issues = loadIssues();

    let csv = "parole_chiave,frequenza,coperte,non_coperte,esempi\n";

    for (const [key, data] of Object.entries(issues)) {
      const examples = data.examples.join(" | ").replace(/"/g, '""');
      csv += `"${key}",${data.count},${data.covered_count},${data.uncovered_count},"${examples}"\n`;
    }

    res.setHeader("Content-Type", "text/csv");
    res.setHeader(
      "Content-Disposition",
      "attachment; filename=analisi_domande_clienti.csv"
    );
    res.send(csv);
  });

  // ===== START =====
  const PORT = 8080;
  app.listen(PORT, () => {
    console.log(`✅ Server attivo su http://localhost:${PORT}`);
  });
}

main().catch(console.error);