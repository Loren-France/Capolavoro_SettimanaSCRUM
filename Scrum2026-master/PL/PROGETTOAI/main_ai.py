import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Optional, Any
import warnings

warnings.filterwarnings('ignore')

class ProductionAnalyzer:

    def predict_demand(self, product_name: str, weeks_ahead: int = 4):
        """
        Prevede la domanda per un prodotto.
    
        Args:
            product_name: Nome del prodotto
            weeks_ahead: Settimane da prevedere

        Returns:
            DataFrame con previsioni
        """
        try:
            from forecast_module import DemandForecaster
        
            # Carica forecaster
            forecaster = DemandForecaster()
        
            # Trova meal_id per il prodotto
            product_info = self.df_combinato[self.df_combinato['nome_pane'] == product_name]
            if product_info.empty:
                raise ValueError(f"Prodotto {product_name} non trovato")
        
            meal_id = product_info['meal_id'].iloc[0]
        
            # Prevedi domanda
            forecast = forecaster.forecast_demand(meal_id, weeks_ahead)
        
            # Converte ordini in kg (assumendo 1 ordine = 2kg in media)
            forecast['predicted_kg'] = forecast['predicted_orders'] * 2
        
            return forecast
        except Exception as e:
            print(f"Errore nella previsione: {e}")
            return pd.DataFrame()

    def generate_demand_report(self, product_name: str = None):
        """
        Genera report di previsione della domanda.
    
        Args:
            product_name: Nome del prodotto

        Returns:
            Dizionario con report
        """
        try:
            from forecast_module import DemandForecaster
        
            # Carica forecaster
            forecaster = DemandForecaster()
        
            if product_name:
                # Trova meal_id per il prodotto
                product_info = self.df_combinato[self.df_combinato['nome_pane'] == product_name]
                if product_info.empty:
                    raise ValueError(f"Prodotto {product_name} non trovato")

                meal_id = product_info['meal_id'].iloc[0]
                report = forecaster.generate_forecast_report(meal_id)
            else:
                # Report per tutti i prodotti
                top_products = self.df_combinato['meal_id'].head(5).tolist()
                report = {}

                for meal_id in top_products:
                    product_report = forecaster.generate_forecast_report(meal_id)
                    if product_report:
                        product_name = self.df_combinato[
                            self.df_combinato['meal_id'] == meal_id
                        ]['nome_pane'].iloc[0]
                        report[product_name] = product_report

            return report
        except Exception as e:
            print(f"Errore generazione report: {e}")
            return {}

    def __init__(self, ingredienti_file: str, produzione_file: str, magazzino_file: str = "data/magazzino.csv"):
        """
        Inizializza l'analizzatore di produzione con i file CSV.
        
        Args:
            ingredienti_file: Path del file ingredienti
            produzione_file: Path del file fasi di produzione
            magazzino_file: Path del file magazzino
        """
        self.ingredienti_file = ingredienti_file
        self.produzione_file = produzione_file
        self.magazzino_file = magazzino_file
        
        # Assicurati che la cartella data esista
        os.makedirs("data", exist_ok=True)
        
        # Carica i dati
        self.df_ingredienti = pd.read_csv(ingredienti_file)
        self.df_produzione = pd.read_csv(produzione_file)
        
        # Rinomina le colonne se necessario (da 'prodotto' a 'nome_pane')
        if 'prodotto' in self.df_ingredienti.columns:
            self.df_ingredienti = self.df_ingredienti.rename(columns={'prodotto': 'nome_pane'})
        if 'prodotto' in self.df_produzione.columns:
            self.df_produzione = self.df_produzione.rename(columns={'prodotto': 'nome_pane'})
        
        # Crea dataframe combinato per analisi
        self._create_combined_dataframe()
        
        # Inizializza o carica magazzino
        self._init_magazzino()
        
        # Dizionario per conversione nomi
        self.meal_id_map = self._create_meal_id_map()
        
    def _create_meal_id_map(self) -> Dict[str, int]:
        """Crea mappa nome_pane -> meal_id basata sul mapping originale"""
        # Nota: I meal_id sono presi dalla tabella fornita
        mapping_data = {
            'Pane casereccio': 1885, 'Pane di Altamura': 1993, 'Pane toscano sciapo': 2539,
            'Pagnotta rustica': 2139, 'Filone bianco': 2631, 'Filone integrale': 1248,
            'Ciabatta classica': 1778, 'Ciabatta ai cereali': 1062, 'Pane pugliese': 2707,
            'Pane cafone napoletano': 1207, 'Pane di segale': 1230, 'Pane ai 5 cereali': 2322,
            'Pane al mais': 2290, 'Pane al farro': 1727, 'Pane al kamut': 1109,
            'Rosetta soffice': 2640, 'Micchetta milanese': 2306, 'Baguette italiana': 2126,
            'Pane tipo ciabattina': 2826, 'Pane al latte': 1754, 'Focaccia genovese': 1971,
            'Focaccia al rosmarino': 1902, 'Focaccia farcita': 1311, 'Schiacciata toscana': 1803,
            'Pane carasau': 1558, 'Pane guttiau': 2581, 'Coppia ferrarese': 1962,
            'Pane mantovano': 1445, 'Pane alla biga': 2444, 'Pane tipo ciabatta rustica': 2867,
            'Pane per tramezzini classico': 1525, 'Pane per tramezzini integrale': 2704,
            'Pane per tramezzini ai cereali': 2304, 'Pane in cassetta bianco': 1247,
            'Pane in cassetta integrale': 1770, 'Pane in cassetta ai semi': 1198,
            'Pane morbido per toast': 2577, 'Pane americano a fette': 1878,
            'Pane sandwich al latte': 1216, 'Pane sandwich maxi fette': 2494,
            'Pan brioche salato': 1847, 'Pan bauletto classico': 2760,
            'Pan bauletto integrale': 1543, 'Pan bauletto ai cereali': 2705,
            'Pane per club sandwich': 2408, 'Pane per toast spessore sottile': 1526,
            'Pane per toast spessore alto': 1344, 'Pane morbido senza crosta': 1567,
            'Pane sandwich proteico': 1963, 'Pane sandwich a lievito madre': 2582,
            'Panino all\'olio': 1439, 'Panino morbido al latte': 1850,
            'Panino rustico ai cereali': 2445, 'Panino tipo rosetta': 2868,
            'Panino ciabattina sandwich': 1886, 'Panino per hot dog': 1994,
            'Bun per burger classico': 2540, 'Bun per burger ai semi': 2140,
            'Bun per burger integrale': 2632, 'Mini bun per slider': 1249,
            'Panino arabo': 1779, 'Piadina classica': 1063, 'Piadina integrale': 2708,
            'Piadina ai cereali': 1208, 'Focaccina morbida': 1231,
            'Panino tipo baguettina': 2323, 'Panino soffice per merenda': 2291,
            'Brioche salata ripiena': 1728, 'Panino alla zucca': 1110,
            'Panino al carbone vegetale': 2641, 'Grissini classici': 2307,
            'Grissini torinesi sottili': 2127, 'Grissini al sesamo': 2827,
            'Grissini al rosmarino': 1755, 'Grissini integrali': 1972,
            'Grissini ai cereali': 1903, 'Grissini stirati a mano': 1312,
            'Grissini alla cipolla': 1804, 'Grissini all\'olio extravergine': 1559,
            'Grissini sfogliati': 2583, 'Crostini dorati': 1964,
            'Crostini all\'aglio': 1446, 'Crostini all\'origano': 2446,
            'Crostini ai cereali': 2869, 'Crostini per zuppe': 1527,
            'Cracker salati classici': 2709, 'Cracker integrali': 2305,
            'Cracker ai semi': 1246, 'Cracker senza lievito': 1771,
            'Cracker al rosmarino': 1199, 'Cracker al mais': 2578,
            'Snack croccante ai cereali': 1879, 'Quadretti di pane tostato': 1217,
            'Sfoglie croccanti al sale': 2495, 'Sfoglie croccanti alle erbes': 1848,
            'Mini cracker per aperitivo': 2761, 'Snack tipo bruschetta': 1544,
            'Bruschettine all\'olio d\'oliva': 2706, 'Bruschettine ai pomodorini': 2409,
            'Bruschettine mediterranee': 1524
        }
        return mapping_data
    
    def _create_combined_dataframe(self):
        """Crea un dataframe combinato per analisi facilitata"""
        # Calcola costo ingredienti per prodotto
        costo_ingredienti = self.calcola_costo_ingredienti_dettaglio()
        
        # Calcola costo produzione per prodotto
        costo_produzione = self.calcola_costo_produzione_dettaglio()
        
        # Unisci i dataframe
        self.df_combinato = pd.merge(
            costo_ingredienti, 
            costo_produzione,
            on='nome_pane',
            how='inner'
        )
        
        # Calcola costo totale
        self.df_combinato['costo_totale_per_100kg'] = (
            self.df_combinato['costo_ingredienti_per_100kg'] + 
            self.df_combinato['costo_produzione_per_100kg']
        )
        
        # Aggiungi meal_id
        self.df_combinato['meal_id'] = self.df_combinato['nome_pane'].map(self._create_meal_id_map())
    
    def _init_magazzino(self):
        """Inizializza o carica il file magazzino"""
        if os.path.exists(self.magazzino_file):
            self.df_magazzino = pd.read_csv(self.magazzino_file)
        else:
            # Crea magazzino iniziale con scorte standard
            ingredienti_unici = self.df_ingredienti['ingrediente'].unique()
            magazzino_data = []
            
            for ingrediente in ingredienti_unici:
                # Assegna scorte iniziali in base al tipo di ingrediente
                if ingrediente == 'Farina':
                    quantita = 5000  # kg
                elif ingrediente == 'Acqua':
                    quantita = 10000  # litri (kg)
                elif ingrediente == 'Lievito':
                    quantita = 200  # kg
                elif ingrediente == 'Sale':
                    quantita = 500  # kg
                elif ingrediente == 'Olio':
                    quantita = 300  # kg
                else:
                    quantita = 100  # kg per ingredienti non specificati
                
                magazzino_data.append({
                    'ingrediente': ingrediente,
                    'quantita_kg': quantita,
                    'scorta_minima': quantita * 0.1,  # 10% della scorta iniziale
                    'data_aggiornamento': datetime.now().strftime('%Y-%m-%d')
                })
            
            self.df_magazzino = pd.DataFrame(magazzino_data)
            self._salva_magazzino()
    
    def _salva_magazzino(self):
        """Salva lo stato del magazzino su file"""
        self.df_magazzino.to_csv(self.magazzino_file, index=False)
    
    def calcola_costo_ingredienti_dettaglio(self) -> pd.DataFrame:
        """
        Calcola il costo degli ingredienti per ogni prodotto in dettaglio.
        
        Returns:
            DataFrame con nome_pane e costo_ingredienti_per_100kg
        """
        # Raggruppa per prodotto e calcola costo
        df_costo = self.df_ingredienti.copy()
        df_costo['costo_ingrediente'] = (
            df_costo['quantita_kg_per_100kg_prodotto'] * 
            df_costo['costo_kg']
        )
        
        # Somma i costi per prodotto
        costo_per_prodotto = df_costo.groupby('nome_pane')['costo_ingrediente'].sum().reset_index()
        costo_per_prodotto.columns = ['nome_pane', 'costo_ingredienti_per_100kg']
        
        # Aggiungi dettaglio ingredienti
        dettaglio = df_costo.pivot_table(
            index='nome_pane',
            columns='ingrediente',
            values='costo_ingrediente',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Unisci costo totale e dettaglio
        risultato = pd.merge(costo_per_prodotto, dettaglio, on='nome_pane')
        
        return risultato
    
    def calcola_costo_produzione_dettaglio(self) -> pd.DataFrame:
        """
        Calcola il costo di produzione per ogni prodotto.
        
        Returns:
            DataFrame con nome_pane e costo_produzione_per_100kg
        """
        # Calcola costo per fase
        df_produzione = self.df_produzione.copy()
        df_produzione['costo_fase'] = (
            (df_produzione['tempo_min_per_batch'] / 60) * 
            df_produzione['costo_orario_macchina']
        )
        
        # Somma i costi per prodotto
        costo_per_prodotto = df_produzione.groupby('nome_pane')['costo_fase'].sum().reset_index()
        costo_per_prodotto.columns = ['nome_pane', 'costo_produzione_per_100kg']
        
        # Aggiungi dettaglio fasi
        dettaglio = df_produzione.pivot_table(
            index='nome_pane',
            columns='fase',
            values='costo_fase',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Unisci costo totale e dettaglio
        risultato = pd.merge(costo_per_prodotto, dettaglio, on='nome_pane')
        
        return risultato
    
    def _calcola_costo_ingredienti(self, nome_pane: str) -> List[Dict]:
        """Calcola il costo dettagliato degli ingredienti per un prodotto"""
        ingredienti_prodotto = self.df_ingredienti[self.df_ingredienti['nome_pane'] == nome_pane]
        ingredienti_costo = []
        
        for _, ingrediente in ingredienti_prodotto.iterrows():
            costo_item = {
                'nome': ingrediente['ingrediente'],
                'quantita_kg': ingrediente['quantita_kg_per_100kg_prodotto'],
                'costo_kg': ingrediente['costo_kg'],
                'costo_totale': ingrediente['quantita_kg_per_100kg_prodotto'] * ingrediente['costo_kg']
            }
            ingredienti_costo.append(costo_item)
        
        return ingredienti_costo
    
    def _calcola_costo_fasi_produzione(self, nome_pane: str) -> List[Dict]:
        """Calcola il costo dettagliato delle fasi di produzione per un prodotto"""
        fasi_prodotto = self.df_produzione[self.df_produzione['nome_pane'] == nome_pane]
        fasi_costo = []
        
        for _, fase in fasi_prodotto.iterrows():
            costo_fase = {
                'fase': fase.get('fase', 'Fase Sconosciuta'),
                'tempo_min': fase.get('tempo_min_per_batch', 0),
                'durata_ore': fase.get('tempo_min_per_batch', 0) / 60,
                'costo_orario': fase.get('costo_orario_macchina', 0),
                'costo_totale': (fase.get('tempo_min_per_batch', 0) / 60) * fase.get('costo_orario_macchina', 0)
            }
            fasi_costo.append(costo_fase)
        
        return fasi_costo
    
    def calcola_costo_totale_prodotto(self, nome_pane):
        """Calcola costo totale per un prodotto specifico"""
        try:
            # Trova il prodotto
            prodotto = self.df_combinato[self.df_combinato['nome_pane'] == nome_pane]
            if prodotto.empty:
                return {"errore": f"Prodotto {nome_pane} non trovato"}
            
            # Calcola costi ingredienti
            ingredienti_costo = self._calcola_costo_ingredienti(nome_pane)
            
            # Calcola costi produzione
            fasi_costo = self._calcola_costo_fasi_produzione(nome_pane)
            
            # Calcola totali
            costo_ingredienti = sum(item.get('costo_totale', 0) for item in ingredienti_costo)
            
            # Calcola costo produzione - gestendo vari formati
            costo_produzione = 0
            for fase in fasi_costo:
                # Cerca il costo totale in vari possibili campi
                if 'costo_totale' in fase:
                    costo_produzione += fase['costo_totale']
                elif 'costo' in fase:
                    costo_produzione += fase['costo']
                # Se non c'è, calcola da durata e costo orario
                elif 'durata_ore' in fase and 'costo_orario' in fase:
                    costo_produzione += fase['durata_ore'] * fase['costo_orario']
                elif 'tempo_min' in fase and 'costo_orario' in fase:
                    costo_produzione += (fase['tempo_min'] / 60) * fase['costo_orario']
            
            costo_totale = costo_ingredienti + costo_produzione
            
            # Assicurati che i dati delle fasi abbiano campi standardizzati
            fasi_processate = []
            for fase in fasi_costo:
                fase_processed = {}
                
                # Nome della fase
                if 'fase' in fase:
                    fase_processed['nome'] = fase['fase']
                elif 'nome' in fase:
                    fase_processed['nome'] = fase['nome']
                elif 'macchina' in fase:
                    fase_processed['nome'] = fase['macchina']
                else:
                    fase_processed['nome'] = 'Fase Sconosciuta'
                
                # Durata in ore
                if 'durata_ore' in fase:
                    fase_processed['durata_ore'] = fase['durata_ore']
                elif 'tempo_min' in fase:
                    fase_processed['durata_ore'] = fase['tempo_min'] / 60
                elif 'tempo' in fase:
                    # Assumiamo che sia in ore se c'è solo 'tempo'
                    fase_processed['durata_ore'] = fase['tempo']
                else:
                    fase_processed['durata_ore'] = 0
                
                # Costo orario
                if 'costo_orario' in fase:
                    fase_processed['costo_orario'] = fase['costo_orario']
                elif 'costo_h' in fase:
                    fase_processed['costo_orario'] = fase['costo_h']
                elif 'costo' in fase and 'durata_ore' in fase_processed and fase_processed['durata_ore'] > 0:
                    # Calcola costo orario dal costo totale
                    fase_processed['costo_orario'] = fase['costo'] / fase_processed['durata_ore']
                else:
                    fase_processed['costo_orario'] = 0
                
                # Calcola costo totale per questa fase
                fase_processed['costo_totale'] = fase_processed['durata_ore'] * fase_processed['costo_orario']
                
                fasi_processate.append(fase_processed)
            
            return {
                'nome_pane': nome_pane,
                'costo_ingredienti': costo_ingredienti,
                'costo_produzione': costo_produzione,
                'costo_totale': costo_totale,
                'ingredienti': ingredienti_costo,
                'fasi': fasi_processate  # Usa le fasi processate invece di quelle originali
            }
        except Exception as e:
            import traceback
            return {"errore": str(e), "traceback": traceback.format_exc()}
    
    def verifica_disponibilita_magazzino(self, nome_pane: str, quantita_kg: float) -> Dict[str, Any]:
        """
        Verifica se ci sono ingredienti sufficienti in magazzino per produrre una quantità specifica.
        
        Args:
            nome_pane: Nome del prodotto
            quantita_kg: Quantità in kg da produrre
            
        Returns:
            Dizionario con disponibilità per ogni ingrediente
        """
        # Ottieni ingredienti del prodotto
        ingredienti_prodotto = self.df_ingredienti[self.df_ingredienti['nome_pane'] == nome_pane]
        
        if ingredienti_prodotto.empty:
            raise ValueError(f"Prodotto {nome_pane} non trovato")
        
        risultato = {
            'prodotto': nome_pane,
            'quantita_richiesta_kg': quantita_kg,
            'disponibile': True,
            'ingredienti': [],
            'ingredienti_mancanti': []
        }
        
        # Fattore di conversione (i dati sono per 100kg di prodotto)
        fattore = quantita_kg / 100
        
        # Verifica ogni ingrediente
        for _, ingrediente in ingredienti_prodotto.iterrows():
            nome_ingrediente = ingrediente['ingrediente']
            quantita_richiesta = ingrediente['quantita_kg_per_100kg_prodotto'] * fattore
            
            # Trova in magazzino
            magazzino_ingrediente = self.df_magazzino[
                self.df_magazzino['ingrediente'] == nome_ingrediente
            ]
            
            if magazzino_ingrediente.empty:
                disponibile = 0
                scorta_minima = 0
            else:
                disponibile = magazzino_ingrediente['quantita_kg'].iloc[0]
                scorta_minima = magazzino_ingrediente['scorta_minima'].iloc[0]
            
            # Verifica disponibilità
            ingrediente_sufficiente = disponibile >= quantita_richiesta
            
            risultato['ingredienti'].append({
                'nome': nome_ingrediente,
                'quantita_richiesta_kg': quantita_richiesta,
                'disponibile_kg': disponibile,
                'sufficiente': ingrediente_sufficiente,
                'scorta_minima_kg': scorta_minima
            })
            
            if not ingrediente_sufficiente:
                risultato['disponibile'] = False
                risultato['ingredienti_mancanti'].append({
                    'ingrediente': nome_ingrediente,
                    'mancante_kg': quantita_richiesta - disponibile
                })
        
        return risultato
    
    def pianifica_produzione(self, ordini: List[Dict[str, float]], 
                           priorita_massimizzazione: str = 'profitto') -> Dict[str, Any]:
        """
        Pianifica la produzione ottimale dati gli ordini e i vincoli di magazzino.
        
        Args:
            ordini: Lista di dizionari {'nome_pane': quantita_kg}
            priorita_massimizzazione: 'profitto' o 'soddisfazione_ordini'
            
        Returns:
            Piano di produzione ottimizzato
        """
        # Crea dataframe ordini
        df_ordini = pd.DataFrame(ordini, columns=['nome_pane', 'quantita_kg'])
        
        # Calcola requisiti totali per ingrediente
        requisiti_totali = {}
        
        for _, ordine in df_ordini.iterrows():
            nome_pane = ordine['nome_pane']
            quantita_kg = ordine['quantita_kg']
            
            # Ottieni ingredienti del prodotto
            ingredienti_prodotto = self.df_ingredienti[
                self.df_ingredienti['nome_pane'] == nome_pane
            ]
            
            for _, ingrediente in ingredienti_prodotto.iterrows():
                nome_ingrediente = ingrediente['ingrediente']
                quantita_per_100kg = ingrediente['quantita_kg_per_100kg_prodotto']
                quantita_necessaria = quantita_per_100kg * (quantita_kg / 100)
                
                if nome_ingrediente not in requisiti_totali:
                    requisiti_totali[nome_ingrediente] = 0
                requisiti_totali[nome_ingrediente] += quantita_necessaria
        
        # Verifica disponibilità magazzino
        piano_produzione = {
            'piano_completo': True,
            'ordini_soddisfatti': [],
            'ordini_parziali': [],
            'ordini_non_soddisfatti': [],
            'vincoli_magazzino': [],
            'utilizzo_ingredienti': {},
            'costo_totale': 0,
            'tempo_totale': 0
        }
        
        # Verifica ogni ingrediente
        for ingrediente, quantita_necessaria in requisiti_totali.items():
            magazzino_ingrediente = self.df_magazzino[
                self.df_magazzino['ingrediente'] == ingrediente
            ]
            
            if magazzino_ingrediente.empty:
                disponibile = 0
            else:
                disponibile = magazzino_ingrediente['quantita_kg'].iloc[0]
            
            piano_produzione['utilizzo_ingredienti'][ingrediente] = {
                'necessario_kg': quantita_necessaria,
                'disponibile_kg': disponibile,
                'sufficiente': disponibile >= quantita_necessaria
            }
            
            if disponibile < quantita_necessaria:
                piano_produzione['piano_completo'] = False
                piano_produzione['vincoli_magazzino'].append({
                    'ingrediente': ingrediente,
                    'necessario_kg': quantita_necessaria,
                    'disponibile_kg': disponibile,
                    'mancante_kg': quantita_necessaria - disponibile
                })
        
        # Se ci sono vincoli, ottimizza in base alla priorità
        if not piano_produzione['piano_completo'] and priorita_massimizzazione == 'profitto':
            # Ottimizzazione per massimizzare il profitto
            piano_produzione = self._ottimizza_per_profitto(df_ordini, requisiti_totali)
        elif not piano_produzione['piano_completo']:
            # Ottimizzazione per soddisfare il maggior numero di ordini
            piano_produzione = self._ottimizza_per_soddisfazione(df_ordini, requisiti_totali)
        
        # Calcola costi e tempi totali
        piano_produzione = self._calcola_costi_tempi_piano(piano_produzione)
        
        return piano_produzione
    
    def _ottimizza_per_profitto(self, df_ordini: pd.DataFrame, 
                               requisiti_totali: Dict[str, float]) -> Dict[str, Any]:
        """Ottimizza la produzione per massimizzare il profitto"""
        # Calcola margine per prodotto (qui semplificato come 1/costo)
        df_ordini['costo_unitario'] = df_ordini['nome_pane'].apply(
            lambda x: self.df_combinato[
                self.df_combinato['nome_pane'] == x
            ]['costo_totale_per_100kg'].iloc[0] / 100 if not self.df_combinato[
                self.df_combinato['nome_pane'] == x
            ].empty else 0
        )
        
        # Ordina per costo unitario (minore costo = maggiore margine)
        df_ordini = df_ordini.sort_values('costo_unitario', ascending=True)
        
        # Implementa logica di ottimizzazione (versione semplificata)
        piano = {
            'piano_completo': False,
            'ordini_soddisfatti': [],
            'ordini_parziali': [],
            'ordini_non_soddisfatti': [],
            'vincoli_magazzino': [],
            'utilizzo_ingredienti': requisiti_totali.copy(),
            'note': 'Piano ottimizzato per massimizzare il profitto'
        }
        
        # Logica semplificata: soddisfa gli ordini a costo minore prima
        for _, ordine in df_ordini.iterrows():
            piano['ordini_soddisfatti'].append({
                'nome_pane': ordine['nome_pane'],
                'quantita_originale_kg': ordine['quantita_kg'],
                'quantita_prodotta_kg': ordine['quantita_kg']
            })
        
        return piano
    
    def _ottimizza_per_soddisfazione(self, df_ordini: pd.DataFrame,
                                   requisiti_totali: Dict[str, float]) -> Dict[str, Any]:
        """Ottimizza per soddisfare il maggior numero di ordini"""
        # Logica semplificata: soddisfa prima gli ordini con minori requisiti
        piano = {
            'piano_completo': False,
            'ordini_soddisfatti': [],
            'ordini_parziali': [],
            'ordini_non_soddisfatti': [],
            'vincoli_magazzino': [],
            'utilizzo_ingredienti': requisiti_totali.copy(),
            'note': 'Piano ottimizzato per soddisfazione ordini'
        }
        
        # Per ogni ordine, verifica se può essere soddisfatto parzialmente
        for _, ordine in df_ordini.iterrows():
            # Verifica disponibilità per questo prodotto
            disponibilita = self.verifica_disponibilita_magazzino(
                ordine['nome_pane'], 
                ordine['quantita_kg']
            )
            
            if disponibilita['disponibile']:
                piano['ordini_soddisfatti'].append({
                    'nome_pane': ordine['nome_pane'],
                    'quantita_originale_kg': ordine['quantita_kg'],
                    'quantita_prodotta_kg': ordine['quantita_kg']
                })
            else:
                # Calcola quantità massima producibile
                quantita_producibile = self._calcola_quantita_producibile(
                    ordine['nome_pane'], 
                    ordine['quantita_kg']
                )
                
                if quantita_producibile > 0:
                    piano['ordini_parziali'].append({
                        'nome_pane': ordine['nome_pane'],
                        'quantita_originale_kg': ordine['quantita_kg'],
                        'quantita_prodotta_kg': quantita_producibile
                    })
                else:
                    piano['ordini_non_soddisfatti'].append({
                        'nome_pane': ordine['nome_pane'],
                        'quantita_originale_kg': ordine['quantita_kg'],
                        'quantita_prodotta_kg': 0,
                        'motivo': 'Ingredienti insufficienti'
                    })
        
        return piano
    
    def _calcola_quantita_producibile(self, nome_pane: str, quantita_desiderata: float) -> float:
        """Calcola la quantità massima producibile dato il magazzino"""
        ingredienti_prodotto = self.df_ingredienti[
            self.df_ingredienti['nome_pane'] == nome_pane
        ]
        
        quantita_max = quantita_desiderata
        
        for _, ingrediente in ingredienti_prodotto.iterrows():
            nome_ingrediente = ingrediente['ingrediente']
            quantita_per_100kg = ingrediente['quantita_kg_per_100kg_prodotto']
            
            magazzino_ingrediente = self.df_magazzino[
                self.df_magazzino['ingrediente'] == nome_ingrediente
            ]
            
            if magazzino_ingrediente.empty:
                disponibile = 0
            else:
                disponibile = magazzino_ingrediente['quantita_kg'].iloc[0]
            
            # Calcola quantità massima con questo ingrediente
            quantita_max_con_ingrediente = (disponibile / quantita_per_100kg) * 100
            
            if quantita_max_con_ingrediente < quantita_max:
                quantita_max = quantita_max_con_ingrediente
        
        return min(quantita_max, quantita_desiderata)
    
    def _calcola_costi_tempi_piano(self, piano: Dict[str, Any]) -> Dict[str, Any]:
        """Calcola costi e tempi totali del piano di produzione"""
        costo_totale = 0
        tempo_totale_min = 0
        
        # Calcola per ordini soddisfatti
        for ordine in piano['ordini_soddisfatti']:
            nome_pane = ordine['nome_pane']
            quantita_kg = ordine['quantita_prodotta_kg']
            
            # Ottieni costo per 100kg
            prodotto = self.df_combinato[self.df_combinato['nome_pane'] == nome_pane]
            
            if not prodotto.empty:
                costo_per_100kg = prodotto['costo_totale_per_100kg'].iloc[0]
                costo_totale += (quantita_kg / 100) * costo_per_100kg
                
                # Calcola tempo (semplificato: somma dei tempi delle fasi)
                fasi_prodotto = self.df_produzione[self.df_produzione['nome_pane'] == nome_pane]
                tempo_prodotto_min = fasi_prodotto['tempo_min_per_batch'].sum()
                # Assumendo che il tempo sia per 100kg
                tempo_totale_min += (quantita_kg / 100) * tempo_prodotto_min
        
        # Calcola per ordini parziali
        for ordine in piano['ordini_parziali']:
            nome_pane = ordine['nome_pane']
            quantita_kg = ordine['quantita_prodotta_kg']
            
            prodotto = self.df_combinato[self.df_combinato['nome_pane'] == nome_pane]
            
            if not prodotto.empty:
                costo_per_100kg = prodotto['costo_totale_per_100kg'].iloc[0]
                costo_totale += (quantita_kg / 100) * costo_per_100kg
                
                fasi_prodotto = self.df_produzione[self.df_produzione['nome_pane'] == nome_pane]
                tempo_prodotto_min = fasi_prodotto['tempo_min_per_batch'].sum()
                tempo_totale_min += (quantita_kg / 100) * tempo_prodotto_min
        
        piano['costo_totale'] = costo_totale
        piano['tempo_totale_ore'] = tempo_totale_min / 60
        piano['tempo_totale_giorni'] = tempo_totale_min / (60 * 8)  # Assumendo 8 ore al giorno
        
        return piano
    
    def aggiorna_magazzino(self, utilizzo: Dict[str, float], 
                          motivo: str = "Produzione") -> bool:
        """
        Aggiorna il magazzino dopo la produzione.
        
        Args:
            utilizzo: Dizionario ingrediente -> quantità utilizzata (kg)
            motivo: Motivo dell'aggiornamento
            
        Returns:
            True se l'aggiornamento è riuscito
        """
        try:
            for ingrediente, quantita_utilizzata in utilizzo.items():
                # Trova l'ingrediente in magazzino
                idx = self.df_magazzino[self.df_magazzino['ingrediente'] == ingrediente].index
                
                if len(idx) > 0:
                    # Aggiorna quantità
                    nuova_quantita = self.df_magazzino.loc[idx[0], 'quantita_kg'] - quantita_utilizzata
                    
                    # Verifica che non scenda sotto zero
                    if nuova_quantita < 0:
                        print(f"Avviso: Quantità negativa per {ingrediente}. Impostata a 0.")
                        nuova_quantita = 0
                    
                    self.df_magazzino.loc[idx[0], 'quantita_kg'] = nuova_quantita
                    self.df_magazzino.loc[idx[0], 'data_aggiornamento'] = datetime.now().strftime('%Y-%m-%d')
            
            # Salva magazzino
            self._salva_magazzino()
            
            # Registra movimento
            self._registra_movimento(utilizzo, motivo)
            
            return True
        except Exception as e:
            print(f"Errore nell'aggiornamento del magazzino: {e}")
            return False
    
    def _registra_movimento(self, utilizzo: Dict[str, float], motivo: str):
        """Registra il movimento nel log magazzino"""
        log_file = "data/magazzino_log.csv"
        log_data = []
        
        for ingrediente, quantita in utilizzo.items():
            log_data.append({
                'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ingrediente': ingrediente,
                'quantita_kg': -quantita,  # Negativo per utilizzo
                'motivo': motivo,
                'tipo': 'USCITA'
            })
        
        df_log = pd.DataFrame(log_data)
        
        if os.path.exists(log_file):
            df_log.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df_log.to_csv(log_file, index=False)
    
    def rifornisci_magazzino(self, rifornimenti: List[Dict[str, float]], 
                            fornitore: str = "Fornitore standard") -> bool:
        """
        Aggiunge ingredienti al magazzino (rifornimento).
        
        Args:
            rifornimenti: Lista di dizionari {'ingrediente': quantita_kg}
            fornitore: Nome del fornitore
            
        Returns:
            True se il rifornimento è riuscito
        """
        try:
            for rifornimento in rifornimenti:
                ingrediente = rifornimento['ingrediente']
                quantita = rifornimento['quantita_kg']
                
                # Trova l'ingrediente in magazzino
                idx = self.df_magazzino[self.df_magazzino['ingrediente'] == ingrediente].index
                
                if len(idx) > 0:
                    # Aggiorna quantità
                    self.df_magazzino.loc[idx[0], 'quantita_kg'] += quantita
                    self.df_magazzino.loc[idx[0], 'data_aggiornamento'] = datetime.now().strftime('%Y-%m-%d')
                else:
                    # Aggiungi nuovo ingrediente
                    nuovo_ingrediente = {
                        'ingrediente': ingrediente,
                        'quantita_kg': quantita,
                        'scorta_minima': quantita * 0.1,
                        'data_aggiornamento': datetime.now().strftime('%Y-%m-%d')
                    }
                    self.df_magazzino = pd.concat(
                        [self.df_magazzino, pd.DataFrame([nuovo_ingrediente])],
                        ignore_index=True
                    )
            
            # Salva magazzino
            self._salva_magazzino()
            
            # Registra movimento di ingresso
            log_file = "data/magazzino_log.csv"
            log_data = []
            
            for rifornimento in rifornimenti:
                log_data.append({
                    'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'ingrediente': rifornimento['ingrediente'],
                    'quantita_kg': rifornimento['quantita_kg'],
                    'motivo': f"Rifornimento da {fornitore}",
                    'tipo': 'INGRESSO'
                })
            
            df_log = pd.DataFrame(log_data)
            
            if os.path.exists(log_file):
                df_log.to_csv(log_file, mode='a', header=False, index=False)
            else:
                df_log.to_csv(log_file, index=False)
            
            return True
        except Exception as e:
            print(f"Errore nel rifornimento del magazzino: {e}")
            return False
    
    def analizza_andamento_cost(self) -> pd.DataFrame:
        """Analizza l'andamento dei costi dei prodotti"""
        df_analisi = self.df_combinato.copy()
        
        # Calcola statistiche
        df_analisi['costo_per_kg'] = df_analisi['costo_totale_per_100kg'] / 100
        
        # Classifica prodotti per costo
        df_analisi = df_analisi.sort_values('costo_per_kg')
        df_analisi['classifica_costo'] = range(1, len(df_analisi) + 1)
        
        # Identifica prodotti più e meno costosi
        df_analisi['categoria_costo'] = pd.qcut(
            df_analisi['costo_per_kg'], 
            q=3, 
            labels=['Basso', 'Medio', 'Alto']
        )
        
        return df_analisi
    
    def suggerisci_ottimizzazioni(self) -> Dict[str, Any]:
        """Suggerisce ottimizzazioni basate sui dati"""
        suggerimenti = {
            'riduzione_costi': [],
            'ottimizzazione_magazzino': [],
            'suggerimenti_produzione': []
        }
        
        # Analizza prodotti più costosi
        df_costosi = self.df_combinato.nlargest(5, 'costo_totale_per_100kg')
        
        for _, prodotto in df_costosi.iterrows():
            nome = prodotto['nome_pane']
            costo = prodotto['costo_totale_per_100kg']
            
            # Analizza componenti del costo
            costo_ingredienti = prodotto.get('costo_ingredienti_per_100kg', 0)
            costo_produzione = prodotto.get('costo_produzione_per_100kg', 0)
            
            if costo_ingredienti > costo * 0.7:  # Se ingredienti > 70% del costo
                suggerimenti['riduzione_costi'].append({
                    'prodotto': nome,
                    'tipo': 'ingredienti',
                    'suggerimento': f'Valutare fornitori alternativi per ingredienti di {nome}'
                })
            
            if costo_produzione > costo * 0.5:  # Se produzione > 50% del costo
                suggerimenti['riduzione_costi'].append({
                    'prodotto': nome,
                    'tipo': 'produzione',
                    'suggerimento': f'Ottimizzare tempi di produzione per {nome}'
                })
        
        # Analizza magazzino
        for _, ingrediente in self.df_magazzino.iterrows():
            if ingrediente['quantita_kg'] < ingrediente['scorta_minima']:
                suggerimenti['ottimizzazione_magazzino'].append({
                    'ingrediente': ingrediente['ingrediente'],
                    'quantita_attuale': ingrediente['quantita_kg'],
                    'scorta_minima': ingrediente['scorta_minima'],
                    'suggerimento': f'Riordinare {ingrediente["ingrediente"]} - scorta bassa'
                })
        
        # Suggerimenti generali
        suggerimenti['suggerimenti_produzione'].extend([
            'Valutare l\'acquisto all\'ingrosso per ingredienti più utilizzati',
            'Ottimizzare la sequenza di produzione per ridurre i tempi di setup',
            'Considerare l\'automazione delle fasi più lunghe'
        ])
        
        return suggerimenti
    
    def genera_report(self) -> Dict[str, Any]:
        """Genera un report completo dell'analisi"""
        report = {
            'data_generazione': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'statistiche_generali': {},
            'top_prodotti': {},
            'stato_magazzino': {},
            'analisi_cost': {},
            'suggerimenti': self.suggerisci_ottimizzazioni()
        }
        
        # Statistiche generali
        report['statistiche_generali'] = {
            'numero_prodotti': len(self.df_combinato),
            'costo_medio_per_100kg': float(self.df_combinato['costo_totale_per_100kg'].mean()),
            'costo_minimo_per_100kg': float(self.df_combinato['costo_totale_per_100kg'].min()),
            'costo_massimo_per_100kg': float(self.df_combinato['costo_totale_per_100kg'].max()),
            'deviazione_standard_cost': float(self.df_combinato['costo_totale_per_100kg'].std())
        }
        
        # Top prodotti per costo
        top5_costosi = self.df_combinato.nlargest(5, 'costo_totale_per_100kg')
        top5_economici = self.df_combinato.nsmallest(5, 'costo_totale_per_100kg')
        
        report['top_prodotti'] = {
            'piu_costosi': top5_costosi[['nome_pane', 'costo_totale_per_100kg']].to_dict('records'),
            'meno_costosi': top5_economici[['nome_pane', 'costo_totale_per_100kg']].to_dict('records')
        }
        
        # Stato magazzino
        report['stato_magazzino'] = {
            'ingredienti_totali': len(self.df_magazzino),
            'valore_totale_scorte': float((self.df_magazzino['quantita_kg'] * 1).sum()),  # Valore approssimativo
            'ingredienti_sotto_scorta': len([
                i for _, i in self.df_magazzino.iterrows() 
                if i['quantita_kg'] < i['scorta_minima']
            ])
        }
        
        # Analisi costi
        df_analisi = self.analizza_andamento_cost()
        report['analisi_cost'] = {
            'distribuzione_costi': {
                'basso': len(df_analisi[df_analisi['categoria_costo'] == 'Basso']),
                'medio': len(df_analisi[df_analisi['categoria_costo'] == 'Medio']),
                'alto': len(df_analisi[df_analisi['categoria_costo'] == 'Alto'])
            },
            'correlazione_ingredienti_produzione': float(
                self.df_combinato['costo_ingredienti_per_100kg'].corr(
                    self.df_combinato['costo_produzione_per_100kg']
                )
            )
        }
        
        return report


# Funzioni di utilità
def carica_dati(ingredienti_file: str, produzione_file: str) -> ProductionAnalyzer:
    """Carica i dati e restituisce un'istanza di ProductionAnalyzer"""
    return ProductionAnalyzer(ingredienti_file, produzione_file)

def salva_dati_json(dati: Dict, filename: str):
    """Salva dati in formato JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)

def carica_dati_json(filename: str) -> Dict:
    """Carica dati da file JSON"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)