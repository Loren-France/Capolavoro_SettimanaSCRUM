import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
import cv2
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ============================
# 1. MODELLI DI PROCESSO
# ============================

def modello_lievitazione(t_min, temperatura, idratazione):
    """
    Modello semplificato di lievitazione:
    - k aumenta con la temperatura
    - volume_max aumenta con l’idratazione
    """
    k = 0.03 + (temperatura - 20) * 0.002
    volume_max = 3 + (idratazione - 60) * 0.05
    return volume_max / (1 + np.exp(-k * (t_min - 60)))


def modello_cottura(t_min, temp_forno):
    """
    Modello semplificato di grado di cottura:
    - cresce con tempo e temperatura
    - limitato tra 0 e 1
    """
    return np.clip((t_min * temp_forno) / 5000, 0, 1)


def valuta_qualita(grado_cottura, volume_finale):
    """
    Valuta qualità finale combinando:
    - stato cottura
    - stato volume
    - giudizio complessivo
    """
    if grado_cottura < 0.4:
        stato_cottura = "Poco cotto"
    elif grado_cottura < 0.8:
        stato_cottura = "Ben cotto"
    else:
        stato_cottura = "Troppo cotto"

    if volume_finale < 1.5:
        stato_volume = "Poco lievitato"
    elif volume_finale < 2.5:
        stato_volume = "Volume buono"
    else:
        stato_volume = "Molto sviluppato"

    if stato_cottura == "Ben cotto" and stato_volume == "Volume buono":
        giudizio = "Qualità ottima"
    elif stato_cottura == "Ben cotto":
        giudizio = "Qualità buona"
    else:
        giudizio = "Qualità da migliorare"

    return stato_cottura, stato_volume, giudizio


# ============================
# 2. YOLO – CARICAMENTO MODELLO
# ============================

@st.cache_resource
def carica_modello_yolo():
    try:
        return YOLO("yolov8n.pt")
    except Exception as e:
        st.error(f"Errore nel caricamento del modello YOLO: {e}")
        return None

model = carica_modello_yolo()

food_classes = {
    "sandwich", "hamburger", "hot dog",
    "pizza", "donut", "cake",
    "fries", "salad",
    "apple", "banana", "orange",
    "bowl", "cup"
}

def è_panino(classi):
    return bool(classi.intersection(food_classes))


# ============================
# 3. DIFETTI DAL COLORE
# ============================

def rileva_difetti_colore(img_array):
    """
    Analisi colore in HSV per:
    - bruciature (zone molto scure)
    - muffa (toni verdi/blu saturi)
    - cottura insufficiente (immagine troppo chiara)
    """
    hsv = cv2.cvtColor(img_array, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    difetti = []

    # Bruciatura: molte zone molto scure
    if np.sum(v < 50) > img_array.size * 0.02:
        difetti.append("Possibile bruciatura (zone molto scure)")

    # Muffa: toni verdi/blu saturi
    mask_muffa = ((h > 60) & (h < 180) & (s > 80))
    if np.sum(mask_muffa) > img_array.size * 0.01:
        difetti.append("Possibile presenza di muffa (colori verde/blu anomali)")

    # Cottura insufficiente: immagine molto chiara
    if np.sum(v > 200) > img_array.size * 0.15:
        difetti.append("Possibile cottura insufficiente (pane molto chiaro)")

    if not difetti:
        difetti.append("Nessun difetto evidente")

    return difetti


# ============================
# 4. ANALISI IMMAGINE + YOLO
# ============================

def analizza_immagine(img_array):
    """
    Usa YOLO per rilevare classi e, se è cibo/panino,
    applica l’analisi difetti colore.
    """
    if model is None:
        return ["Modello YOLO non disponibile: analisi non eseguita."], set()

    try:
        risultati = model(img_array)
    except Exception as e:
        return [f"Errore durante l’analisi YOLO: {e}"], set()

    classi_trovate = set()

    for r in risultati:
        if not hasattr(r, "boxes") or r.boxes is None:
            continue
        for box in r.boxes:
            cls = int(box.cls[0])
            classi_trovate.add(model.names[cls])

    if è_panino(classi_trovate):
        problemi = rileva_difetti_colore(img_array)
    else:
        if classi_trovate:
            problemi = ["Nessun panino rilevato: analisi difetti specifica non applicata."]
        else:
            problemi = ["Nessun oggetto rilevato dall’AI."]

    return problemi, classi_trovate


# ============================
# 5. CONSIGLI DI MIGLIORAMENTO
# ============================

def genera_consigli(stato_cottura, stato_volume,
                    temperatura_liev, idratazione,
                    temp_forno, tempo_cottura_min, tempo_liev_min):
    consigli = []

    # Cottura
    if stato_cottura == "Poco cotto":
        consigli.append("Aumentare il tempo di cottura o alzare leggermente la temperatura del forno.")
    elif stato_cottura == "Ben cotto":
        consigli.append("La cottura è buona: mantenere questi parametri.")
    elif stato_cottura == "Troppo cotto":
        consigli.append("Ridurre la temperatura del forno o accorciare il tempo di cottura.")

    # Volume / lievitazione
    if stato_volume == "Poco lievitato":
        consigli.append("Aumentare la temperatura di lievitazione o prolungare il tempo di riposo.")
        if temperatura_liev < 26:
            consigli.append("La temperatura di lievitazione è bassa: portarla tra 26°C e 30°C.")
        if idratazione < 60:
            consigli.append("Aumentare leggermente l’idratazione dell’impasto.")
    elif stato_volume == "Volume buono":
        consigli.append("La lievitazione è corretta: mantenere questi parametri.")
    elif stato_volume == "Molto sviluppato":
        consigli.append("Ridurre leggermente l’idratazione per evitare eccessiva espansione.")
        if temperatura_liev > 32:
            consigli.append("La temperatura di lievitazione è alta: abbassarla sotto i 30°C.")

    # Controlli aggiuntivi su forno e tempi
    if temp_forno < 180:
        consigli.append("La temperatura del forno è bassa: aumentarla per una cottura più uniforme.")
    if temp_forno > 250:
        consigli.append("La temperatura del forno è molto alta: rischio bruciatura.")

    if tempo_cottura_min < 10:
        consigli.append("Il tempo di cottura è molto breve: aumentarlo per una cottura completa.")
    if tempo_cottura_min > 40:
        consigli.append("Il tempo di cottura è molto lungo: rischio di seccare il prodotto.")

    if tempo_liev_min < 60:
        consigli.append("Il tempo di lievitazione è breve: aumentarlo per un volume migliore.")
    if tempo_liev_min > 180:
        consigli.append("Il tempo di lievitazione è molto lungo: rischio di sovralievitazione.")

    return consigli


# ============================
# 6. PDF REPORT
# ============================

def genera_report_pdf(fig, params, stato_cottura, stato_volume,
                      giudizio, problemi, consigli, is_panino):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Titolo
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h - 50, "Report qualità pane / panino")

    y = h - 90
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Parametri simulazione:")
    y -= 15

    # Parametri
    for k, v in params.items():
        c.drawString(60, y, f"- {k}: {v}")
        y -= 12

    y -= 10
    c.drawString(50, y, f"Cottura: {stato_cottura}")
    y -= 12
    c.drawString(50, y, f"Volume: {stato_volume}")
    y -= 12
    c.drawString(50, y, f"Giudizio finale: {giudizio}")
    y -= 20

    c.drawString(50, y, f"Panino rilevato: {'Sì' if is_panino else 'No'}")
    y -= 20

    # Difetti
    c.drawString(50, y, "Difetti rilevati:")
    y -= 12
    for p in problemi:
        c.drawString(60, y, f"- {p}")
        y -= 12

    y -= 10
    c.drawString(50, y, "Consigli:")
    y -= 12
    for cons in consigli:
        c.drawString(60, y, f"- {cons}")
        y -= 12

    # Pagina grafici
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="PNG", bbox_inches="tight")
    img_buf.seek(0)
    img = ImageReader(img_buf)

    c.showPage()
    c.drawImage(img, 50, 200, width=500, height=300)

    c.save()
    buffer.seek(0)
    return buffer


# ============================
# 7. INTERFACCIA STREAMLIT
# ============================

st.title("🍞 Digital Twin + AI per Panini e Pane")
st.caption("Simulazione di lievitazione e cottura con riconoscimento difetti tramite AI e analisi colore.")

# ---- STILE GRAFICO ----
st.markdown("""
    <style>
        .box {
            padding: 15px;
            border-radius: 10px;
            background-color: #f7f3e9;
            border: 1px solid #e0d6c3;
            margin-bottom: 15px;
        }
        .title {
            font-size: 20px;
            font-weight: bold;
            color: #5a4634;
            margin-bottom: 8px;
        }
        .item {
            font-size: 16px;
            color: #4a3f35;
            margin-left: 10px;
        }
        .good {
            color: #2e7d32;
            font-weight: bold;
        }
        .warning {
            color: #ed6c02;
            font-weight: bold;
        }
        .bad {
            color: #c62828;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="box"><div class="title">🎯 Obiettivo</div>'
    '<div class="item">Simulare il processo di panificazione e valutare la qualità del prodotto '
    'tramite AI e analisi del colore.</div></div>',
    unsafe_allow_html=True
)

# ---- PARAMETRI DI PROCESSO ----
st.header("⚙️ Parametri di processo")

col1, col2 = st.columns(2)

with col1:
    temperatura_liev = st.slider("Temperatura lievitazione (°C)", 20, 40, 28)
    idratazione = st.slider("Idratazione (%)", 50, 90, 65)
    tempo_liev_min = st.slider("Tempo lievitazione (min)", 30, 240, 120)

with col2:
    temp_forno = st.slider("Temperatura forno (°C)", 150, 280, 220)
    tempo_cottura_min = st.slider("Tempo cottura (min)", 5, 60, 25)

# ---- SIMULAZIONI ----
st.header("📈 Simulazione lievitazione e cottura")

t_liev = np.linspace(0, tempo_liev_min, 200)
volume = modello_lievitazione(t_liev, temperatura_liev, idratazione)

t_cott = np.linspace(0, tempo_cottura_min, 200)
grado_cottura_curve = modello_cottura(t_cott, temp_forno)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(t_liev, volume)
ax[0].set_title("Lievitazione")
ax[0].set_xlabel("Tempo (min)")
ax[0].set_ylabel("Volume relativo")

ax[1].plot(t_cott, grado_cottura_curve, color='orange')
ax[1].set_title("Cottura")
ax[1].set_xlabel("Tempo (min)")
ax[1].set_ylabel("Grado di cottura")

plt.tight_layout()
st.pyplot(fig)

stato_cottura, stato_volume, giudizio = valuta_qualita(grado_cottura_curve[-1], volume[-1])

st.markdown(
    f'<div class="box"><div class="title">📊 Valutazione simulazione</div>'
    f'<div class="item">Cottura: <b>{stato_cottura}</b></div>'
    f'<div class="item">Volume: <b>{stato_volume}</b></div>'
    f'<div class="item">Giudizio complessivo: <b>{giudizio}</b></div></div>',
    unsafe_allow_html=True
)

# ---- UPLOAD IMMAGINE ----
st.header("🖼️ Analisi immagine prodotto")

file = st.file_uploader("Carica un'immagine (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

problemi = []
classi = set()
is_panino = False

if file is not None:
    img_bytes = file.read()
    img_array = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)

    if img_array is not None:
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        st.image(img_rgb, caption="Immagine caricata", use_column_width=True)

        problemi, classi = analizza_immagine(img_array)
        is_panino = è_panino(classi)


        # Difetti
        if problemi:
            st.markdown('<div class="box"><div class="title">🔍 Difetti rilevati</div>', unsafe_allow_html=True)
            for p in problemi:
                colore = (
                    "bad" if "bruciatura" in p or "muffa" in p else
                    "warning" if "chiaro" in p else
                    "good"
                )
                st.markdown(f'<div class="item {colore}">• {p}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.error("Impossibile leggere l’immagine caricata.")

# ---- CONSIGLI ----
st.header("💡 Consigli di miglioramento")

consigli = genera_consigli(
    stato_cottura,
    stato_volume,
    temperatura_liev,
    idratazione,
    temp_forno,
    tempo_cottura_min,
    tempo_liev_min
)

st.markdown('<div class="box"><div class="title">Suggerimenti basati su simulazione e parametri</div>', unsafe_allow_html=True)
for c in consigli:
    st.markdown(f'<div class="item">• {c}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- PARAMETRI RIEPILOGO ----
params = {
    "Temperatura lievitazione (°C)": temperatura_liev,
    "Idratazione (%)": idratazione,
    "Tempo lievitazione (min)": tempo_liev_min,
    "Temperatura forno (°C)": temp_forno,
    "Tempo cottura (min)": tempo_cottura_min,
}

st.header("📋 Riepilogo parametri")

st.markdown('<div class="box"><div class="title">Parametri utilizzati</div>', unsafe_allow_html=True)
for k, v in params.items():
    st.markdown(f'<div class="item">• <b>{k}</b>: {v}</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- PDF ----
st.header("📄 Report PDF")

if st.button("Genera PDF"):
    if fig is None:
        st.error("Grafico non disponibile per il report.")
    else:
        pdf = genera_report_pdf(
            fig,
            params,
            stato_cottura,
            stato_volume,
            giudizio,
            problemi if problemi else ["Nessun difetto analizzato o immagine non caricata."],
            consigli,
            is_panino
        )
        st.download_button("Scarica PDF", pdf, "report_panino.pdf", mime="application/pdf")
# ============================