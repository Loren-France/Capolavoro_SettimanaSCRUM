import pandas as pd
from pathlib import Path

# Cartella dove sono i CSV
BASE = Path(__file__).parent / "data"

train_path = BASE / "train.csv"
pani_path = BASE / "pani.csv"

print("Leggo:", train_path)
print("Leggo:", pani_path)

# 1) Carico i dati
train = pd.read_csv(train_path)
pani = pd.read_csv(pani_path)

print("Colonne train:", list(train.columns))
print("Colonne pani:", list(pani.columns))

# 2) Trovo quali meal_id mancano in train
existing_ids = set(train["meal_id"].unique())
all_ids = set(pani["meal_id"].unique())
missing_ids = sorted(all_ids - existing_ids)

print("Meal_id esistenti in train:", len(existing_ids))
print("Meal_id in pani:", len(all_ids))
print("Meal_id mancanti da generare:", len(missing_ids))
print("Prime 10 mancanti:", missing_ids[:10])

if not missing_ids:
    print("Non ci sono meal_id mancanti: train_new.csv sarà uguale a train.csv")
    train_new = train.copy()
else:
    # 3) Scegli un meal_id di riferimento (storico reale simile)
    #    qui prendo l'ULTIMO meal_id presente in train
    ref_id = max(existing_ids)
    print("Uso come riferimento il meal_id:", ref_id)

    ref_hist = train[train["meal_id"] == ref_id].copy()

    if ref_hist.empty:
        raise ValueError(
            f"Nessuno storico trovato in train.csv per il meal_id di riferimento {ref_id}"
        )

    # 4) Genero storico sintetico per ogni meal_id mancante
    rows = []
    for new_id in missing_ids:
        tmp = ref_hist.copy()
        tmp["meal_id"] = new_id
        # opzionale: scala la domanda se vuoi (es. 0.8 per 80%)
        fattore = 1.0
        if "num_orders" in tmp.columns:
            tmp["num_orders"] = (tmp["num_orders"] * fattore).round().astype(int)
        rows.append(tmp)

    synth = pd.concat(rows, ignore_index=True)
    print("Righe sintetiche create:", len(synth))

    # 5) Concateno train originale + righe sintetiche
    train_new = pd.concat([train, synth], ignore_index=True)

# 6) Salvo il nuovo file
out_path = BASE / "train_new.csv"
train_new.to_csv(out_path, index=False)

print("Salvato nuovo file:", out_path)
print("Shape originale:", train.shape, " -> Shape nuovo:", train_new.shape)
