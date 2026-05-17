import pandas as pd
from prophet import Prophet


PATH_TRAIN = "data/train.csv"
PATH_PANI = "data/pani.csv"



def main():
    # 1) Carico vendite
    print("Carico il dataset di vendite...")
    df = pd.read_csv(PATH_TRAIN)
    print("Prime 5 righe di train.csv:")
    print(df.head())


    # 2) Carico elenco prodotti (pani.csv) e costruisco dizionario nome -> meal_id
    df_pani = pd.read_csv(PATH_PANI)
    mappa_pani = dict(zip(df_pani["nome_pane"], df_pani["meal_id"]))


    print("\nProdotti disponibili:")
    nomi_pani = list(mappa_pani.keys())
    for i, nome in enumerate(nomi_pani, start=1):
        print(f"{i}. {nome}")


    scelta = int(input("\nSeleziona il numero del prodotto: "))
    if scelta < 1 or scelta > len(nomi_pani):
        raise ValueError("Scelta non valida.")


    nome_pane = nomi_pani[scelta - 1]
    meal_target = mappa_pani[nome_pane]


    print(f"\nHai scelto: {nome_pane} (meal_id interno = {meal_target})")


    # 3) Filtro i dati per quel meal_id
    d = df[df["meal_id"] == meal_target].copy()
    if d.empty:
        raise ValueError("Nessun dato trovato per questo meal_id nel train.csv.")


    print(f"\nNumero di righe trovate per meal_id = {meal_target}: {len(d)}")


    # 4) Preparo la serie temporale per Prophet
    # 'week' è un numero di settimana: creo una data fittizia a partire da una base
    base_date = pd.to_datetime("2015-01-01")
    d["ds"] = d["week"].apply(lambda w: base_date + pd.to_timedelta(int(w), unit="W"))
    d["y"] = d["num_orders"]


    d = d[["ds", "y"]].sort_values("ds")


    print("\nPrime 10 righe dei dati usati per il modello:")
    print(d.head(10))


    # 5) Alleno il modello Prophet
    print("\nAlleno il modello di previsione (Prophet), attendi...")
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=False,
        yearly_seasonality=True
    )
    model.fit(d)
    print("Modello allenato.")


    # 6) Previsioni future
    future_weeks = int(input("\nQuante settimane future vuoi prevedere? (es. 12): "))
    future = model.make_future_dataframe(periods=future_weeks, freq="W")
    forecast = model.predict(future)


    result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(future_weeks)


    print(f"\nPrevisioni domanda (pezzi) per le prossime {future_weeks} settimane per {nome_pane}:")
    print(result)


    # 7) Salvo su CSV
    output_name = f"forecast_{meal_target}.csv"
    result.to_csv(output_name, index=False)
    print(f"\nPrevisioni salvate nel file: {output_name}")



if __name__ == "__main__":
    main()