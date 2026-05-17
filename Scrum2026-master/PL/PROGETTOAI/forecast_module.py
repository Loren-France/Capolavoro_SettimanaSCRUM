import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class DemandForecaster:
    def __init__(self, train_file: str = "data/train_new.csv", 
                 product_file: str = "data/pani.csv"):
        """
        Inizializza il sistema di previsione della domanda ottimizzato per grandi dataset.
        """
        self.train_file = train_file
        self.product_file = product_file
        
        # Carica dati in modo efficiente
        self._load_data()
        
        # Cache per modelli addestrati
        self.models_cache = {}
        self.scalers_cache = {}
        
    def _load_data(self):
        """Carica dati in modo efficiente usando chunking"""
        try:
            print(f"Caricamento {self.train_file}...")
            # Carica solo le colonne necessarie per ridurre memoria
            self.train_data = pd.read_csv(
                self.train_file, 
                usecols=['week', 'center_id', 'meal_id', 'checkout_price', 
                        'base_price', 'emailer_for_promotion', 'homepage_featured', 'num_orders']
            )
            print(f"Dati caricati: {len(self.train_data):,} righe")
            
            # Carica prodotti
            self.product_data = pd.read_csv(self.product_file)
            
            # Unisci con nomi prodotti
            if 'meal_id' in self.product_data.columns:
                # Standardizza nomi colonne
                if 'nome' in self.product_data.columns:
                    self.product_data = self.product_data.rename(columns={'nome': 'nome_pane'})
                
                # Unisci
                self.combined_data = pd.merge(
                    self.train_data,
                    self.product_data[['meal_id', 'nome_pane']],
                    on='meal_id',
                    how='left'
                )
                
                # Sostituisci NaN
                self.combined_data['nome_pane'] = self.combined_data['nome_pane'].fillna('Sconosciuto')
                
                print(f"Prodotti unici: {self.combined_data['nome_pane'].nunique():,}")
                
            else:
                self.combined_data = self.train_data.copy()
                self.combined_data['nome_pane'] = 'Sconosciuto'
            
            # Calcola features derivate
            self._calculate_features()
            
        except Exception as e:
            print(f"Errore caricamento dati: {e}")
            # Fallback a dataset vuoto
            self.combined_data = pd.DataFrame()
    
    def _calculate_features(self):
        """Calcola features derivate per migliorare previsioni"""
        if len(self.combined_data) == 0:
            return
            
        # Prezzo relativo
        self.combined_data['price_ratio'] = (
            self.combined_data['checkout_price'] / 
            self.combined_data['base_price'].replace(0, 1)
        ).clip(0.5, 2.0)  # Clip per valori estremi
        
        # Promozione attiva
        self.combined_data['promo_active'] = (
            self.combined_data['emailer_for_promotion'] | 
            self.combined_data['homepage_featured']
        ).astype(int)
        
        # Settimana dell'anno (per stagionalità)
        self.combined_data['week_of_year'] = self.combined_data['week'] % 52
        
        # Differenza prezzo
        self.combined_data['price_discount'] = (
            self.combined_data['base_price'] - self.combined_data['checkout_price']
        )
        
        print("Features calcolate con successo")
    
    def get_top_products(self, n: int = 10):
        """Restituisce i prodotti più venduti"""
        if len(self.combined_data) == 0:
            return pd.DataFrame()
        
        top_products = (self.combined_data
                       .groupby(['meal_id', 'nome_pane'])
                       .agg({'num_orders': 'sum', 'week': 'nunique'})
                       .reset_index()
                       .sort_values('num_orders', ascending=False)
                       .head(n))
        
        top_products.columns = ['meal_id', 'nome_pane', 'ordini_totali', 'settimane_dati']
        
        return top_products
    
    def get_product_stats(self, product_id: int = None, product_name: str = None):
        """Ottiene statistiche per un prodotto"""
        if product_id:
            data = self.combined_data[self.combined_data['meal_id'] == product_id]
        elif product_name:
            data = self.combined_data[self.combined_data['nome_pane'] == product_name]
        else:
            data = self.combined_data
        
        if len(data) == 0:
            return {}
        
        stats = {
            'total_orders': int(data['num_orders'].sum()),
            'avg_weekly_orders': float(data['num_orders'].mean()),
            'max_weekly_orders': int(data['num_orders'].max()),
            'min_weekly_orders': int(data['num_orders'].min()),
            'std_orders': float(data['num_orders'].std()),
            'weeks_of_data': int(data['week'].nunique()),
            'centers': int(data['center_id'].nunique()),
            'avg_price': float(data['checkout_price'].mean()),
            'promo_weeks': int(data['promo_active'].sum())
        }
        
        # Calcola trend recente (ultime 4 settimane)
        latest_week = data['week'].max()
        recent_data = data[data['week'] > (latest_week - 4)]
        
        if len(recent_data) > 1:
            stats['recent_trend'] = float(
                recent_data.groupby('week')['num_orders'].mean().diff().mean()
            )
        else:
            stats['recent_trend'] = 0
        
        return stats
    
    def train_model_for_product(self, product_id: int, sample_size: int = 10000):
        """Addestra modello per un prodotto specifico (con sampling per grandi dataset)"""
        # Controlla cache
        cache_key = f"product_{product_id}"
        if cache_key in self.models_cache:
            return self.models_cache[cache_key], self.scalers_cache[cache_key]
        
        # Filtra dati prodotto
        product_data = self.combined_data[self.combined_data['meal_id'] == product_id]
        
        if len(product_data) < 20:
            return None, None
        
        # Campiona se necessario
        if len(product_data) > sample_size:
            product_data = product_data.sample(sample_size, random_state=42)
        
        # Prepara features
        features = ['week', 'center_id', 'checkout_price', 'base_price', 
                   'emailer_for_promotion', 'homepage_featured', 
                   'price_ratio', 'promo_active', 'week_of_year', 'price_discount']
        
        X = product_data[features]
        y = product_data['num_orders']
        
        # Rimuovi NaN
        mask = ~X.isna().any(axis=1) & ~y.isna()
        X = X[mask]
        y = y[mask]
        
        if len(X) < 10:
            return None, None
        
        # Standardizza
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Addestra modello semplice (Random Forest)
        model = RandomForestRegressor(
            n_estimators=50,  # Ridotto per performance
            max_depth=10,
            random_state=42,
            n_jobs=-1  # Usa tutti i core
        )
        
        model.fit(X_scaled, y)
        
        # Salva in cache
        self.models_cache[cache_key] = model
        self.scalers_cache[cache_key] = scaler
        
        return model, scaler
    
    def forecast_demand(self, product_id: int, weeks_ahead: int = 4, 
                       center_id: int = 55, base_price: float = None):
        """Prevede domanda per un prodotto"""
        # Ottieni dati prodotto
        product_data = self.combined_data[self.combined_data['meal_id'] == product_id]
        
        if product_data.empty:
            return pd.DataFrame()
        
        # Nome prodotto
        product_name = product_data['nome_pane'].iloc[0] if 'nome_pane' in product_data.columns else 'Sconosciuto'
        
        # Valori default
        if base_price is None:
            base_price = product_data['base_price'].median()
        
        last_week = product_data['week'].max()
        forecasts = []
        
        # Addestra o recupera modello
        model, scaler = self.train_model_for_product(product_id)
        
        for week in range(1, weeks_ahead + 1):
            future_week = last_week + week
            
            # Features per previsione
            features_dict = {
                'week': future_week,
                'center_id': center_id,
                'checkout_price': base_price * 0.95,
                'base_price': base_price,
                'emailer_for_promotion': 0,
                'homepage_featured': 0,
                'price_ratio': 0.95,
                'promo_active': 0,
                'week_of_year': future_week % 52,
                'price_discount': base_price * 0.05
            }
            
            X_future = pd.DataFrame([features_dict])
            
            if model is not None and scaler is not None:
                try:
                    X_scaled = scaler.transform(X_future)
                    prediction = model.predict(X_scaled)[0]
                except:
                    # Fallback alla media storica
                    prediction = product_data['num_orders'].mean()
            else:
                # Fallback alla media storica
                prediction = product_data['num_orders'].mean()
            
            # Assicura predizione positiva
            prediction = max(0, prediction)
            
            forecasts.append({
                'week': future_week,
                'week_date': self._week_to_date(future_week),
                'center_id': center_id,
                'meal_id': product_id,
                'nome_pane': product_name,
                'predicted_orders': int(round(prediction, 0)),
                'predicted_kg': int(round(prediction * 2, 0)),  # Assumendo 2kg per ordine
                'base_price': round(base_price, 2),
                'checkout_price': round(base_price * 0.95, 2),
                'confidence': self._calculate_confidence(product_data)
            })
        
        return pd.DataFrame(forecasts)
    
    def _week_to_date(self, week_number: int):
        """Converte numero settimana in data approssimativa"""
        try:
            # Assumendo che la settimana 1 sia la prima settimana del 2023
            base_date = datetime(2023, 1, 1)
            target_date = base_date + timedelta(weeks=week_number - 1)
            return target_date.strftime('%d/%m/%Y')
        except:
            return f"Settimana {week_number}"
    
    def _calculate_confidence(self, product_data: pd.DataFrame):
        """Calcola livello di confidenza per le previsioni"""
        if len(product_data) < 10:
            return "Basso"
        
        cv = product_data['num_orders'].std() / product_data['num_orders'].mean()
        
        if cv < 0.2:
            return "Alto"
        elif cv < 0.5:
            return "Medio"
        else:
            return "Basso"
    
    def analyze_seasonality(self, product_id: int):
        """Analizza stagionalità per un prodotto"""
        product_data = self.combined_data[self.combined_data['meal_id'] == product_id]
        
        if product_data.empty:
            return {}
        
        # Analisi per settimana dell'anno
        product_data['week_of_year'] = product_data['week'] % 52
        
        weekly_pattern = product_data.groupby('week_of_year').agg({
            'num_orders': ['mean', 'sum', 'count']
        }).round(2)
        
        weekly_pattern.columns = ['media_ordini', 'totale_ordini', 'conteggio_settimane']
        weekly_pattern = weekly_pattern.reset_index()
        
        # Trova picchi stagionali
        if len(weekly_pattern) > 0:
            peak_week = weekly_pattern.loc[weekly_pattern['media_ordini'].idxmax()]
            
            # Calcola trend
            try:
                z = np.polyfit(weekly_pattern['week_of_year'], weekly_pattern['media_ordini'], 1)
                trend_slope = z[0]
            except:
                trend_slope = 0
        else:
            peak_week = None
            trend_slope = 0
        
        return {
            'weekly_pattern': weekly_pattern.to_dict('records'),
            'trend_slope': trend_slope,
            'trend_direction': 'Crescente' if trend_slope > 0.1 else 
                              'Decrescente' if trend_slope < -0.1 else 'Stabile',
            'peak_week': peak_week.to_dict() if peak_week is not None else None,
            'seasonality_score': self._calculate_seasonality_score(weekly_pattern)
        }
    
    def _calculate_seasonality_score(self, weekly_pattern: pd.DataFrame):
        """Calcola punteggio di stagionalità"""
        if len(weekly_pattern) < 2:
            return 0
        
        cv = weekly_pattern['media_ordini'].std() / weekly_pattern['media_ordini'].mean()
        
        if cv > 0.7:
            return "Alta stagionalità"
        elif cv > 0.3:
            return "Media stagionalità"
        else:
            return "Bassa stagionalità"
    
    def compare_products(self, product_ids: list, weeks_ahead: int = 4):
        """Confronta previsioni per più prodotti"""
        comparisons = []
        
        for product_id in product_ids:
            forecast = self.forecast_demand(product_id, weeks_ahead)
            
            if not forecast.empty:
                product_name = forecast['nome_pane'].iloc[0]
                total_orders = forecast['predicted_orders'].sum()
                avg_orders = forecast['predicted_orders'].mean()
                
                comparisons.append({
                    'product_id': product_id,
                    'product_name': product_name,
                    'total_predicted': int(total_orders),
                    'avg_predicted': float(avg_orders),
                    'peak_week': forecast.loc[forecast['predicted_orders'].idxmax(), 'week'],
                    'confidence': forecast['confidence'].iloc[0]
                })
        
        return pd.DataFrame(comparisons)

def load_forecaster():
    """Carica il forecast manager"""
    try:
        return DemandForecaster()
    except Exception as e:
        print(f"Errore caricamento forecaster: {e}")
        # Fallback a forecaster vuoto
        return DemandForecaster()