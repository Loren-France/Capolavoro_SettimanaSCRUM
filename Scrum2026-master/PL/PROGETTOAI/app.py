import streamlit as st
import plotly
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import sys
import locale


# Imposta locale italiano per formattazione numeri
try:
    locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Italian_Italy.1252')
    except:
        pass  # Fallback se locale non disponibile

# Funzioni di formattazione numeri stile italiano
def fmt_numero(valore, decimali=0):
    """Formatta numero con separatore migliaia ' e decimali con ,"""
    if decimali == 0:
        return locale.format_string("%.0f", valore, grouping=True).replace(',', "'")
    else:
        formatted = locale.format_string(f"%.{decimali}f", valore, grouping=True)
        formatted = formatted.replace('.', ',').replace(',', "'", formatted.count("'"))
        return formatted

def fmt_euro(valore, decimali=2):
    """Formatta numero come euro con stile italiano"""
    return f"€{fmt_numero(valore, decimali)}"

def fmt_percentuale(valore, decimali=1):
    """Formatta numero come percentuale con stile italiano"""
    return f"{fmt_numero(valore, decimali)}%"
from main_ai import ProductionAnalyzer, carica_dati

# ============================================
# SISTEMA DI LOG MOVIMENTI - ATTIVATO
# ============================================
LOG_ATTIVO = True  # LOG ATTIVATI

def registra_log(tipo, descrizione, dettagli=""):
    """Funzione per registrare i movimenti - ATTIVA"""
    if not LOG_ATTIVO:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Inizializza se non esiste
    if 'log_movimenti' not in st.session_state:
        st.session_state.log_movimenti = []
    
    log_entry = {
        "timestamp": timestamp,
        "tipo": tipo,
        "descrizione": descrizione,
        "dettagli": dettagli
    }
    
    # Aggiungi il log
    st.session_state.log_movimenti.append(log_entry)
    
    # Mantieni solo gli ultimi 200 log
    if len(st.session_state.log_movimenti) > 200:
        st.session_state.log_movimenti = st.session_state.log_movimenti[-200:]
    
    return log_entry

def mostra_pannello_log():
    """Mostra il pannello dei log nella sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Log Movimenti - ATTIVO")
    
    if st.sidebar.button("🗑️ Pulisci Log", key="clear_logs_sidebar_unique"):
        if 'log_movimenti' in st.session_state:
            st.session_state.log_movimenti = []
        st.rerun()
    
    # Mostra ultimi 10 log in sidebar
    if 'log_movimenti' in st.session_state and st.session_state.log_movimenti:
        ultimi_log = st.session_state.log_movimenti[-10:]  # Ultimi 10
        st.sidebar.caption(f"**Ultimi {len(ultimi_log)} movimenti:**")
        
        for log in reversed(ultimi_log):
            icona = "✅" if log['tipo'] == 'SUCCESSO' else "❌" if log['tipo'] == 'ERRORE' else "ℹ️" if log['tipo'] == 'INFO' else "⚠️"
            st.sidebar.caption(f"{icona} **{log['tipo']}**: {log['descrizione']}")
            if log['dettagli']:
                st.sidebar.caption(f"   ↳ {log['dettagli'][:50]}...")
    else:
        st.sidebar.info("Nessun log registrato")

# ============================================
# FUNZIONI DI ANALISI COSTI MIGLIORATE
# ============================================

def analisi_costi_globale_migliorata():
    """Genera analisi costi completa con visualizzazioni migliorate"""
    try:
        analyzer = st.session_state.analyzer
        df = analyzer.df_combinato.copy()
        
        # Calcola costo per kg
        df['Costo per kg (€)'] = df['costo_totale_per_100kg'] / 100
        df['Costo per 100kg (€)'] = df['costo_totale_per_100kg']
        
        # 1. Top 10 Prodotti più Costosi
        top_10_costosi = df.nlargest(10, 'Costo per kg (€)')[['nome_pane', 'Costo per kg (€)', 'Costo per 100kg (€)']]
        top_10_costosi['Posizione'] = range(1, 11)
        
        # Grafico prodotti costosi migliorato
        fig_costosi = px.bar(
            top_10_costosi,
            x='Costo per kg (€)',
            y='nome_pane',
            orientation='h',
            title='� Top 10 Prodotti più Costosi (€/kg)',
            labels={'Costo per kg (€)': 'Costo per kg (€)', 'nome_pane': 'Prodotto'},
            color='Costo per kg (€)',
            color_continuous_scale='Reds',
            hover_data=['Costo per 100kg (€)'],
            text='Costo per kg (€)'
        )
        
        fig_costosi.update_traces(
            texttemplate='€%{x:.2f}'.replace('.', ','),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Costo/kg: €%{x:.2f}<br>Costo/100kg: €%{customdata[0]:.2f}<extra></extra>'
        )
        fig_costosi.update_layout(
            height=500,
            showlegend=False,
            xaxis_title="Costo per kg (€)",
            yaxis_title="",
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='closest',
            font=dict(size=11)
        )
        
        # 2. Top 10 Prodotti più Economici
        top_10_economici = df.nsmallest(10, 'Costo per kg (€)')[['nome_pane', 'Costo per kg (€)', 'Costo per 100kg (€)']]
        top_10_economici['Posizione'] = range(1, 11)
        
        # Grafico prodotti economici migliorato
        fig_economici = px.bar(
            top_10_economici,
            x='Costo per kg (€)',
            y='nome_pane',
            orientation='h',
            title='� Top 10 Prodotti più Economici (€/kg)',
            labels={'Costo per kg (€)': 'Costo per kg (€)', 'nome_pane': 'Prodotto'},
            color='Costo per kg (€)',
            color_continuous_scale='Greens',
            hover_data=['Costo per 100kg (€)'],
            text='Costo per kg (€)'
        )
        
        fig_economici.update_traces(
            texttemplate='€%{x:.2f}'.replace('.', ','),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Costo/kg: €%{x:.2f}<br>Costo/100kg: €%{customdata[0]:.2f}<extra></extra>'
        )
        fig_economici.update_layout(
            height=500,
            showlegend=False,
            xaxis_title="Costo per kg (€)",
            yaxis_title="",
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='closest',
            font=dict(size=11)
        )
        
        # 3. Distribuzione Categorie Costo con etichette migliorate
        # Crea categorie in base ai percentili
        p25 = df['Costo per kg (€)'].quantile(0.25)
        p50 = df['Costo per kg (€)'].quantile(0.50)
        p75 = df['Costo per kg (€)'].quantile(0.75)
        
        def categorizza_costo(costo):
            if costo <= p25:
                return '💰 Economici'
            elif costo <= p50:
                return '💵 Medio-Bassi'
            elif costo <= p75:
                return '💸 Medio-Altri'
            else:
                return '💎 Premium'
        
        df['categoria'] = df['Costo per kg (€)'].apply(categorizza_costo)
        categoria_costi = df['categoria'].value_counts()
        
        # Grafico a torta distribuzione categorie migliorato
        fig_categorie = go.Figure(data=[go.Pie(
            labels=categoria_costi.index,
            values=categoria_costi.values,
            hole=.4,
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{value} prodotti<br>(%{percent})',
            marker_colors=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C'],
            hovertemplate='<b>%{label}</b><br>Prodotti: %{value}<br>Percentuale: %{percent}<extra></extra>'
        )])
        
        fig_categorie.update_layout(
            title='📊 Distribuzione Prodotti per Fascia di Costo',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                font=dict(size=11)
            ),
            height=470,
            font=dict(size=11),
            paper_bgcolor='white'
        )
        
        # 4. Distribuzione completa costi (istogramma)
        fig_distribuzione = px.histogram(
            df,
            x='Costo per kg (€)',
            nbins=15,
            title='📈 Distribuzione dei Costi Unitari per kg',
            labels={'Costo per kg (€)': 'Costo per kg (€)', 'count': 'Numero Prodotti'},
            color_discrete_sequence=['#36A2EB'],
            opacity=0.85
        )
        
        # Aggiungi linee per i percentili
        colors = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']
        percentiles = [('Q1 (25%)', p25), ('Mediana (50%)', p50), ('Q3 (75%)', p75)]
        
        for i, (label, value) in enumerate(percentiles):
            fig_distribuzione.add_vline(
                x=value,
                line_dash="dash",
                line_color=colors[i],
                line_width=2.5,
                annotation_text=f"<b>{label}: {fmt_euro(value, 2)}</b>",
                annotation_position="top right" if i < 2 else "top left",
                annotation_font_size=10
            )
        
        fig_distribuzione.update_layout(
            height=430,
            showlegend=False,
            bargap=0.1,
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='x unified',
            font=dict(size=11),
            xaxis_title="Costo per kg (€)",
            yaxis_title="Numero di Prodotti"
        )
        
        fig_distribuzione.update_traces(
            hovertemplate='Range: €%{x:.2f}<br>Prodotti: %{y}<extra></extra>'
        )
        
        # 5. Correlazione costi ingredienti vs produzione
        fig_correlazione = px.scatter(
            df,
            x='costo_ingredienti_per_100kg',
            y='costo_produzione_per_100kg',
            size='Costo per 100kg (€)',
            color='Costo per kg (€)',
            hover_name='nome_pane',
            title='🔗 Correlazione Costi: Ingredienti vs Produzione',
            labels={
                'costo_ingredienti_per_100kg': 'Costo Ingredienti (€/100kg)',
                'costo_produzione_per_100kg': 'Costo Produzione (€/100kg)',
                'Costo per kg (€)': 'Costo/kg (€)'
            },
            size_max=35,
            color_continuous_scale='Plasma'
        )
        
        fig_correlazione.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                          'Ingredienti: €%{x:.2f}<br>' +
                          'Produzione: €%{y:.2f}<br>' +
                          'Costo/kg: €%{marker.color:.2f}<extra></extra>'
        )
        
        fig_correlazione.update_layout(
            height=500,
            coloraxis_colorbar=dict(title="Costo/kg (€)"),
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='closest',
            font=dict(size=11),
            xaxis_title="Costo Ingredienti (€/100kg)",
            yaxis_title="Costo Produzione (€/100kg)"
        )
        
        registra_log("ANALISI", "Analisi costi globale migliorata generata")
        
        return {
            "top_10_costosi": top_10_costosi,
            "top_10_economici": top_10_economici,
            "categoria_costi": categoria_costi,
            "fig_costosi": fig_costosi,
            "fig_economici": fig_economici,
            "fig_categorie": fig_categorie,
            "fig_distribuzione": fig_distribuzione,
            "fig_correlazione": fig_correlazione,
            "statistiche": {
                "media_costo_kg": df['Costo per kg (€)'].mean(),
                "mediana_costo_kg": df['Costo per kg (€)'].median(),
                "std_costo_kg": df['Costo per kg (€)'].std(),
                "range_costo_kg": df['Costo per kg (€)'].max() - df['Costo per kg (€)'].min(),
                "percentile_25": p25,
                "percentile_50": p50,
                "percentile_75": p75
            }
        }
        
    except Exception as e:
        registra_log("ERRORE", "Errore analisi costi globale migliorata", str(e))
        st.error(f"Errore nell'analisi costi: {str(e)}")
        return None

# ============================================
# FUNZIONI DI PREVISIONE
# ============================================

def load_forecast_data():
    """Carica i dati per le previsioni in modo efficiente."""
    try:
        train_path = "data/train_new.csv"
        pani_path = "data/pani.csv"
        
        if not os.path.exists(train_path):
            st.warning(f"File {train_path} non trovato. Usando train.csv...")
            train_path = "data/train.csv"
        
        usecols = ['week', 'center_id', 'meal_id', 'checkout_price', 
                  'base_price', 'emailer_for_promotion', 'homepage_featured', 'num_orders']
        
        train_data = pd.read_csv(train_path, usecols=usecols)
        pani_data = pd.read_csv(pani_path)
        
        if 'nome' in pani_data.columns:
            pani_data = pani_data.rename(columns={'nome': 'nome_pane'})
        
        combined_data = pd.merge(
            train_data,
            pani_data[['meal_id', 'nome_pane']],
            on='meal_id',
            how='left'
        )
        combined_data['nome_pane'] = combined_data['nome_pane'].fillna('Sconosciuto')
        
        registra_log("PREVISIONI", f"Dati caricati: {len(combined_data):,} righe")
        return combined_data
        
    except Exception as e:
        registra_log("ERRORE", "Errore caricamento dati previsioni", str(e))
        return pd.DataFrame()

def get_product_forecast(product_name, weeks_ahead=4):
    """Genera previsione semplice per un prodotto."""
    try:
        if 'forecast_data' not in st.session_state:
            st.session_state.forecast_data = load_forecast_data()
        
        data = st.session_state.forecast_data
        
        if data.empty:
            return pd.DataFrame()
        
        product_data = data[data['nome_pane'] == product_name]
        
        if product_data.empty:
            st.warning(f"Prodotto '{product_name}' non trovato nei dati storici.")
            return pd.DataFrame()
        
        meal_id = product_data['meal_id'].iloc[0]
        avg_orders = product_data['num_orders'].mean()
        last_week = product_data['week'].max()
        
        forecasts = []
        
        for week in range(1, weeks_ahead + 1):
            future_week = last_week + week
            
            try:
                base_date = datetime(2023, 1, 1)
                target_date = base_date + timedelta(weeks=future_week - 1)
                week_date = target_date.strftime('%d/%m/%Y')
            except:
                week_date = f"Settimana {future_week}"
            
            variation = np.random.uniform(0.85, 1.15)
            predicted_orders = max(10, int(avg_orders * variation))
            
            forecasts.append({
                'Settimana': future_week,
                'Data': week_date,
                'Prodotto': product_name,
                'Ordini_Previsti': predicted_orders,
                'Kg_Previsti': predicted_orders * 2,
                'Confidenza': 'Media' if len(product_data) > 20 else 'Bassa'
            })
        
        forecast_df = pd.DataFrame(forecasts)
        registra_log("PREVISIONI", f"Previsione generata per {product_name}", f"Settimane: {weeks_ahead}")
        
        return forecast_df
        
    except Exception as e:
        registra_log("ERRORE", f"Errore previsione {product_name}", str(e))
        return pd.DataFrame()

def get_top_products_forecast(n=10):
    """Restituisce i prodotti più venduti con statistiche."""
    try:
        if 'forecast_data' not in st.session_state:
            st.session_state.forecast_data = load_forecast_data()
        
        data = st.session_state.forecast_data
        
        if data.empty:
            return pd.DataFrame()
        
        top_products = (data
                       .groupby(['meal_id', 'nome_pane'])
                       .agg({'num_orders': 'sum', 'week': 'nunique'})
                       .reset_index()
                       .sort_values('num_orders', ascending=False)
                       .head(n))
        
        top_products.columns = ['meal_id', 'nome_pane', 'ordini_totali', 'settimane_dati']
        top_products['ordini_settimanali_medi'] = (top_products['ordini_totali'] / 
                                                   top_products['settimane_dati']).round(0)
        
        registra_log("PREVISIONI", f"Top {n} prodotti calcolati")
        return top_products
        
    except Exception as e:
        registra_log("ERRORE", "Errore calcolo top prodotti", str(e))
        return pd.DataFrame()

# ============================================
# FUNZIONE PAGINA PREVISIONI
# ============================================

def show_forecast_page():
    """Pagina per le previsioni di mercato."""
    st.header("🔮 Previsioni di Mercato")
    
    # Verifica file esistenti
    data_files = {
        "Dati vendite": ["data/train_new.csv", "data/train.csv"],
        "Mappatura prodotti": ["data/pani.csv"]
    }
    
    missing_files = []
    for desc, files in data_files.items():
        found = any(os.path.exists(f) for f in files)
        if not found:
            missing_files.append(desc)
    
    if missing_files:
        st.error(f"File mancanti: {', '.join(missing_files)}")
        st.info("""
        Per utilizzare le previsioni, assicurati di avere nella cartella `data/`:
        - `train_new.csv` o `train.csv` (dati storici vendite)
        - `pani.csv` (mappatura prodotti)
        """)
        return
    
    # Carica dati
    with st.spinner("Caricamento dati storici..."):
        forecast_data = load_forecast_data()
    
    if forecast_data.empty:
        st.error("Impossibile caricare i dati per le previsioni.")
        return
    
    # Statistiche
    total_rows = len(forecast_data)
    unique_products = forecast_data['nome_pane'].nunique()
    total_orders = forecast_data['num_orders'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Record Storici", f"{total_rows:,}")
    with col2:
        st.metric("Prodotti Unici", unique_products)
    with col3:
        st.metric("Ordini Totali", f"{total_orders:,}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Previsione Prodotto", "📈 Analisi Trend", "🏆 Top Prodotti"])
    
    with tab1:
        st.subheader("Previsione per Singolo Prodotto")
        
        available_products = forecast_data['nome_pane'].dropna().unique()
        
        if len(available_products) == 0:
            st.warning("Nessun prodotto disponibile nei dati.")
            return
        
        selected_product = st.selectbox(
            "Seleziona prodotto:",
            available_products[:50],
            index=0,
            key="forecast_product_select"
        )
        
        if selected_product:
            product_data = forecast_data[forecast_data['nome_pane'] == selected_product]
            
            if not product_data.empty:
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    total_orders = product_data['num_orders'].sum()
                    st.metric("Ordini Totali", f"{total_orders:,}")
                with col_stat2:
                    avg_weekly = product_data['num_orders'].mean()
                    st.metric("Media Settimanale", fmt_numero(avg_weekly, 0))
                with col_stat3:
                    weeks_data = product_data['week'].nunique()
                    st.metric("Settimane Dati", weeks_data)
            
            col_param1, col_param2 = st.columns(2)
            with col_param1:
                weeks_ahead = st.slider("Settimane da prevedere:", 1, 8, 4)
            with col_param2:
                confidence = st.select_slider("Livello confidenza:", 
                                            options=["Bassa", "Media", "Alta"],
                                            value="Media")
            
            if st.button("🎯 Genera Previsione", type="primary"):
                with st.spinner("Calcolando previsione..."):
                    forecast_df = get_product_forecast(selected_product, weeks_ahead)
                    
                    if not forecast_df.empty:
                        st.success(f"✅ Previsione generata per {selected_product}")
                        
                        total_pred = forecast_df['Ordini_Previsti'].sum()
                        avg_pred = forecast_df['Ordini_Previsti'].mean()
                        
                        col_pred1, col_pred2 = st.columns(2)
                        with col_pred1:
                            st.metric("Ordini Previsti Totali", f"{total_pred:,}")
                        with col_pred2:
                            st.metric("Produzione Stimata (kg)", f"{total_pred * 2:,}")
                        
                        # Grafico migliorato
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=forecast_df['Data'],
                            y=forecast_df['Ordini_Previsti'],
                            name='Previsioni',
                            marker_color='#36A2EB',
                            text=forecast_df['Ordini_Previsti'],
                            textposition='auto',
                            hovertemplate='<b>%{x}</b><br>Ordini: %{y}<br>Kg: %{customdata}<extra></extra>',
                            customdata=forecast_df['Kg_Previsti']
                        ))
                        
                        fig.update_layout(
                            title=f"📈 Previsione Ordini: {selected_product}",
                            xaxis_title="Settimana",
                            yaxis_title="Ordini Previsti",
                            height=400,
                            showlegend=False,
                            plot_bgcolor='rgba(240, 240, 240, 0.5)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tabella migliorata
                        st.dataframe(
                            forecast_df,
                            use_container_width=True,
                            column_config={
                                "Settimana": st.column_config.NumberColumn(
                                    "Settimana",
                                    format="%d"
                                ),
                                "Data": st.column_config.TextColumn(
                                    "Data",
                                    help="Data stimata"
                                ),
                                "Prodotto": st.column_config.TextColumn(
                                    "Prodotto"
                                ),
                                "Ordini_Previsti": st.column_config.NumberColumn(
                                    "Ordini Previsti",
                                    format="%d",
                                    help="Numero di ordini previsti"
                                ),
                                "Kg_Previsti": st.column_config.NumberColumn(
                                    "Kg Previsti",
                                    format="%d kg",
                                    help="Chilogrammi da produrre"
                                ),
                                "Confidenza": st.column_config.TextColumn(
                                    "Affidabilità",
                                    help="Livello di affidabilità della previsione"
                                )
                            }
                        )
                        
                        # Raccomandazioni
                        st.subheader("💡 Raccomandazioni Produzione")
                        
                        if total_pred > avg_weekly * weeks_ahead * 1.2:
                            st.info("""
                            **📈 Considera aumentare la produzione:**
                            - Domanda prevista superiore alla media storica
                            - Verifica disponibilità ingredienti
                            - Pianifica eventuali turni aggiuntivi
                            """)
                        elif total_pred < avg_weekly * weeks_ahead * 0.8:
                            st.warning("""
                            **📉 Valuta riduzione produzione:**
                            - Domanda prevista inferiore alle attese
                            - Considera promozioni per stimolare vendite
                            - Rivedi piani di produzione
                            """)
                        else:
                            st.success("""
                            **⚖️ Mantieni produzione attuale:**
                            - Domanda in linea con le attese
                            - Continua con i livelli produttivi correnti
                            - Monitora settimanalmente l'andamento
                            """)
    
    with tab2:
        st.subheader("Analisi Trend Prodotti")
        
        # Inizializza session state per trend analysis
        if 'trend_analysis_active' not in st.session_state:
            st.session_state.trend_analysis_active = False
        
        col_btn1, col_btn2 = st.columns([2, 1])
        
        with col_btn1:
            if st.button("📈 Analizza Trend Mercato", key="analyze_trends_btn", type="primary"):
                st.session_state.trend_analysis_active = True
                registra_log("ANALISI", "Trend analysis avviato")
        
        with col_btn2:
            if st.session_state.trend_analysis_active:
                if st.button("🔄 Resetta", key="reset_trend_btn"):
                    st.session_state.trend_analysis_active = False
                    registra_log("ANALISI", "Trend analysis resettato")
                    st.rerun()
        
        if st.session_state.trend_analysis_active:
            with st.spinner("Analizzando trend di mercato..."):
                try:
                    top_products = get_top_products_forecast(10)
                    
                    if not top_products.empty:
                        st.success("✅ Analisi trend completata!")
                        st.write("**📊 Top 10 Prodotti per Vendite:**")
                        
                        for idx, (_, row) in enumerate(top_products.iterrows(), 1):
                            col_t1, col_t2, col_t3, col_t4 = st.columns([1, 3, 2, 1])
                            with col_t1:
                                st.write(f"**#{idx}**")
                            with col_t2:
                                st.write(row['nome_pane'])
                            with col_t3:
                                st.write(f"{row['ordini_totali']:,} ordini")
                            with col_t4:
                                avg_weekly = row['ordini_settimanali_medi']
                                st.write(f"{avg_weekly:.0f}/sett.")
                            
                            if idx < 10:
                                st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
                        
                        # Insight
                        st.subheader("🔍 Insight Mercato")
                        
                        total_market = top_products['ordini_totali'].sum()
                        avg_per_product = top_products['ordini_settimanali_medi'].mean()
                        
                        col_insight1, col_insight2, col_insight3 = st.columns(3)
                        with col_insight1:
                            st.metric("Mercato Totale", f"{total_market:,}", "ordini")
                        with col_insight2:
                            st.metric("Media Settimanale", fmt_numero(avg_per_product, 0), "ordini/prodotto")
                        with col_insight3:
                            top_3_share = top_products.head(3)['ordini_totali'].sum() / total_market * 100
                            st.metric("Quota Top 3", fmt_percentuale(top_3_share, 1))
                        
                        # Consigli strategici
                        st.info("""
                        **🎯 Strategie Produzione:**
                        
                        1. **Concentra risorse** sui prodotti top (80% dei ricavi)
                        2. **Mantieni scorte** per prodotti più venduti
                        3. **Monitora prodotti emergenti** per nuove opportunità
                        4. **Valuta bundle** con prodotti complementari
                        """)
                    
                except Exception as e:
                    st.error(f"Errore nell'analisi: {str(e)}")
    
    with tab3:
        st.subheader("Classifica Prodotti")
        
        n_products = st.slider("Prodotti in classifica:", 5, 25, 10)
        
        with st.spinner("Generando classifica..."):
            top_products = get_top_products_forecast(n_products)
        
        if not top_products.empty:
            # Grafico migliorato
            fig = px.bar(
                top_products,
                x='ordini_totali',
                y='nome_pane',
                orientation='h',
                title=f'🏆 Top {n_products} Prodotti per Vendite',
                labels={'ordini_totali': 'Ordini Totali', 'nome_pane': 'Prodotto'},
                color='ordini_totali',
                color_continuous_scale='Viridis',
                hover_data=['settimane_dati', 'ordini_settimanali_medi'],
                text='ordini_totali'
            )
            
            fig.update_traces(
                texttemplate='%{x:,}',
                textposition='outside'
            )
            
            fig.update_layout(
                xaxis_tickangle=0,
                height=500 + (n_products * 15),
                showlegend=False,
                xaxis_title="Ordini Totali",
                yaxis_title="",
                yaxis={'categoryorder': 'total ascending'},
                margin=dict(l=0, r=0, t=50, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabella dettagliata migliorata
            with st.expander("📋 Dettaglio Completo Classifica", expanded=False):
                display_df = top_products.copy()
                display_df['ordini_totali'] = display_df['ordini_totali'].astype(int)
                display_df['ordini_settimanali_medi'] = display_df['ordini_settimanali_medi'].astype(int)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    column_config={
                        "nome_pane": st.column_config.TextColumn(
                            "Prodotto",
                            width="large"
                        ),
                        "ordini_totali": st.column_config.NumberColumn(
                            "Ordini Totali",
                            format="%.0f",
                            width="medium"
                        ),
                        "settimane_dati": st.column_config.NumberColumn(
                            "Settimane Dati",
                            format="%d",
                            width="small"
                        ),
                        "ordini_settimanali_medi": st.column_config.NumberColumn(
                            "Media Settimanale",
                            format="%.0f",
                            width="small"
                        )
                    },
                    hide_index=True
                )

# Registra avvio app
registra_log("INIZIO", "Applicazione avviata", f"Timestamp: {datetime.now()}")

# Configurazione pagina
st.set_page_config(
    page_title="Analisi Produzione Panificio",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stili CSS personalizzati migliorati
st.markdown("""
<style>
    /* Metriche migliorate */
    .stMetric {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #FF4B4B;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Titoli */
    h1, h2, h3 {
        color: #2C3E50 !important;
    }
    
    /* Tabs migliorati */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f0f2f6;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(255, 75, 75, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B;
        color: white !important;
    }
    
    /* Bottoni */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Dataframe migliorato */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Alert migliorati */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Scrollbar personalizzata */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    /* Spaziature */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Log nella sidebar */
    .log-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 6px 0;
        font-size: 0.9em;
    }
    
    .log-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 6px 0;
        font-size: 0.9em;
    }
    
    .log-info {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 6px 0;
        font-size: 0.9em;
    }
    
    /* Tooltip */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Titolo applicazione
st.title("🍞 Analisi Produzione - Panificio Italiano")
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 20px; 
            border-radius: 12px; 
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
    <h2 style='color: white !important; margin-bottom: 10px;'>Dashboard di Analisi Integrata</h2>
    <p style='margin-bottom: 0; opacity: 0.9;'>Monitora costi, gestisci magazzino e pianifica la produzione in un'unica piattaforma</p>
</div>
""", unsafe_allow_html=True)

# Funzione per caricamento dati con cache
@st.cache_data(ttl=3600)
def load_analyzer():
    try:
        analyzer = carica_dati(
            "data/bom.csv",        # File ingredienti (Bill of Materials)
            "data/ciclo.csv"       # File cicli di produzione
        )
        registra_log("CARICAMENTO", "Dati caricati con successo", "File BOM e ciclo produzione")
        return analyzer, True
    except FileNotFoundError as e:
        registra_log("ERRORE", "File non trovato", str(e))
        st.error(f"File non trovato: {e}")
        return None, False
    except Exception as e:
        registra_log("ERRORE", "Errore nel caricamento dati", str(e))
        st.error(f"Errore nel caricamento dati: {str(e)}")
        return None, False

# Funzione di validazione dati
def validate_analyzer(analyzer):
    if analyzer is None:
        return False
    
    required_data = {
        'df_combinato': ['nome_pane', 'costo_ingredienti_per_100kg', 
                        'costo_produzione_per_100kg', 'costo_totale_per_100kg'],
        'df_magazzino': ['ingrediente', 'quantita_kg', 'scorta_minima'],
        'df_ingredienti': ['nome_pane', 'ingrediente', 'quantita_kg_per_100kg_prodotto']
    }
    
    for attr, columns in required_data.items():
        if not hasattr(analyzer, attr):
            registra_log("ERRORE", f"Attributo mancante: {attr}")
            st.error(f"Attributo mancante: {attr}")
            return False
        
        df = getattr(analyzer, attr)
        if df is None or df.empty:
            registra_log("ERRORE", f"DataFrame {attr} vuoto o non valido")
            st.error(f"DataFrame {attr} vuoto o non valido")
            return False
        
        missing = [col for col in columns if col not in df.columns]
        if missing:
            registra_log("ERRORE", f"Colonne mancanti in {attr}: {missing}")
            st.error(f"Colonne mancanti in {attr}: {missing}")
            return False
    
    registra_log("VALIDAZIONE", "Validazione dati completata con successo")
    return True

# Inizializzazione session state
if 'analyzer_loaded' not in st.session_state:
    with st.spinner("Caricamento dati in corso..."):
        analyzer, loaded = load_analyzer()
        
        if loaded and analyzer is not None and validate_analyzer(analyzer):
            st.session_state.analyzer = analyzer
            st.session_state.analyzer_loaded = True
            st.session_state.dati_caricati = True
            registra_log("SUCCESSO", "Sistema inizializzato con successo")
        else:
            st.session_state.analyzer_loaded = False
            st.session_state.dati_caricati = False
            registra_log("ERRORE", "Inizializzazione sistema fallita")

# Inizializza stati per funzionalità specifiche
session_defaults = {
    'ordini_pianificazione': [],
    'rifornimenti': [],
    'selected_product': None,
    'last_report': None,
    'filter_stock_low': False,
    'log_movimenti': [],
    'analisi_costi_data': None,
    'impostazioni': {
        'lingua': 'Italiano',
        'fuso_orario': 'Europe/Rome',
        'notifiche': True
    }
}

for key, default in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Sidebar per navigazione
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046857.png", width=100)
    st.title("Navigazione")
    
    # Lista pagine con previsioni
    pagine_disponibili = ["📊 Dashboard", "💰 Analisi Costi", "📦 Gestione Magazzino", 
                         "📋 Pianificazione Produzione", "📈 Report & Analytics",
                         "🔮 Previsioni Mercato", "⚙️ Configurazione", "📋 Log Sistema"]
    
    pagina = st.radio(
        "Seleziona sezione:",
        pagine_disponibili,
        key="main_navigation"
    )
    
    st.markdown("---")
    
    # Informazioni sistema
    if st.session_state.dati_caricati:
        analyzer = st.session_state.analyzer
        st.info(f"""
        **Panificio Italiano**
        
        🍞 Prodotti: **{len(analyzer.df_combinato)}**
        📦 Ingredienti: **{len(analyzer.df_magazzino)}**
        ✅ Stato: **Operativo**
        📋 Log: **{len(st.session_state.log_movimenti)} registrati**
        """)
    else:
        st.warning("⚠️ Sistema non pronto")
    
    # Mostra pannello log nella sidebar
    mostra_pannello_log()
    
    st.markdown("---")
    
    # Pulsante ricarica
    if st.button("🔄 Ricarica Dati", use_container_width=True):
        registra_log("SISTEMA", "Ricarica dati avviata")
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            if key != 'log_movimenti':  # Mantieni i log durante la ricarica
                del st.session_state[key]
        st.rerun()

# Contenuto principale basato sulla selezione
if not st.session_state.dati_caricati:
    st.warning("""
    ⚠️ Impossibile caricare i dati. 
    
    Verifica che:
    1. I file CSV siano presenti nella cartella 'data'
    2. I file abbiano il formato corretto
    3. I nomi dei file siano 'bom.csv' e 'ciclo.csv'
    """)
    
    # Opzione per caricare file manualmente
    with st.expander("🔄 Caricamento manuale file"):
        col1, col2 = st.columns(2)
        
        with col1:
            bom_file = st.file_uploader("Carica file BOM (ingredienti)", type=['csv'])
        
        with col2:
            ciclo_file = st.file_uploader("Carica file ciclo produzione", type=['csv'])
        
        if bom_file and ciclo_file:
            if st.button("Carica file manuali", type="primary"):
                try:
                    registra_log("CARICAMENTO", "Caricamento manuale file", 
                               f"BOM: {bom_file.name}, Ciclo: {ciclo_file.name}")
                    
                    # Salva i file temporaneamente
                    with open("temp_bom.csv", "wb") as f:
                        f.write(bom_file.getvalue())
                    
                    with open("temp_ciclo.csv", "wb") as f:
                        f.write(ciclo_file.getvalue())
                    
                    # Prova a caricare
                    temp_analyzer = carica_dati("temp_bom.csv", "temp_ciclo.csv")
                    if validate_analyzer(temp_analyzer):
                        st.session_state.analyzer = temp_analyzer
                        st.session_state.dati_caricati = True
                        registra_log("SUCCESSO", "Dati caricati manualmente con successo")
                        st.success("✅ Dati caricati con successo!")
                        st.rerun()
                except Exception as e:
                    registra_log("ERRORE", "Errore caricamento manuale", str(e))
                    st.error(f"Errore: {str(e)}")
else:
    analyzer = st.session_state.analyzer
    
    if pagina == "📊 Dashboard":
        st.header("📊 Dashboard Panoramica")
        registra_log("PAGINA", "Accesso Dashboard")
        
        # Metriche chiave
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            prodotti_totali = len(analyzer.df_combinato)
            st.metric(
                label="🍞 Prodotti Totali",
                value=fmt_numero(prodotti_totali),
                delta="prodotti",
                help="Numero totale di prodotti disponibili"
            )
        
        with col2:
            costo_medio = analyzer.df_combinato['costo_totale_per_100kg'].mean()
            st.metric(
                label="💰 Costo Medio",
                value=fmt_euro(costo_medio, 2),
                delta="per 100kg",
                help="Costo medio di produzione per 100kg di prodotto"
            )
        
        with col3:
            ingredienti_totali = len(analyzer.df_magazzino)
            st.metric(
                label="📦 Ingredienti",
                value=fmt_numero(ingredienti_totali),
                delta="tipi",
                help="Numero di ingredienti diversi in magazzino"
            )
        
        with col4:
            scorte_basse = sum(analyzer.df_magazzino['quantita_kg'] < analyzer.df_magazzino['scorta_minima'])
            st.metric(
                label="⚠️ Scorte Basse",
                value=fmt_numero(scorte_basse),
                delta=f"su {fmt_numero(ingredienti_totali)}",
                delta_color="inverse",
                help="Ingredienti sotto la scorta minima di sicurezza"
            )
        
        st.markdown("---")
        
        # Grafico costi prodotti migliorato
        st.subheader("📈 Analisi Costi Prodotti")
        
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            # Prepara dati per grafico
            df_costi = analyzer.df_combinato.copy()
            df_costi = df_costi.sort_values('costo_totale_per_100kg', ascending=False).head(15)
            
            # Calcola costo per kg per tooltip
            df_costi['Costo per kg'] = df_costi['costo_totale_per_100kg'] / 100
            
            # Crea colori in base al costo medio
            df_costi['colore_categoria'] = df_costi['costo_totale_per_100kg'].apply(
                lambda x: 'Sopra media' if x > costo_medio else 'Sotto media'
            )
            
            fig = px.bar(
                df_costi,
                x='costo_totale_per_100kg',
                y='nome_pane',
                orientation='h',
                title='📊 Top 15 Prodotti per Costo di Produzione',
                labels={'costo_totale_per_100kg': 'Costo per 100kg (€)', 'nome_pane': 'Prodotto'},
                color='colore_categoria',
                color_discrete_map={'Sopra media': '#E74C3C', 'Sotto media': '#27AE60'},
                hover_data={'Costo per kg': ':.2f', 'colore_categoria': False},
                text='costo_totale_per_100kg'
            )
            
            fig.update_traces(
                texttemplate=fmt_euro(fig.data[0].x[0] if hasattr(fig.data[0].x, '__getitem__') else 0, 2),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Costo/100kg: €%{x:.2f}<br>Costo/kg: €%{customdata[0]:.2f}<extra></extra>'
            )
            
            # Aggiungi linea del costo medio
            fig.add_vline(x=costo_medio, line_dash="dash", line_color="orange", line_width=2,
                         annotation_text=f"<b>Media: {fmt_euro(costo_medio, 2)}</b>",
                         annotation_position="top right",
                         annotation_font_size=11)
            
            fig.update_layout(
                height=520,
                showlegend=True,
                xaxis_title="Costo per 100kg (€)",
                yaxis_title="Prodotto",
                plot_bgcolor='rgba(240,240,240,0.3)',
                hovermode='closest',
                font=dict(size=11),
                legend=dict(
                    title="Categoria",
                    yanchor="top",
                    y=0.99,
                    xanchor="right",
                    x=0.99
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.subheader("🏆 Prodotti più Economici")
            df_economici = analyzer.df_combinato.nsmallest(5, 'costo_totale_per_100kg')
            
            for idx, (_, row) in enumerate(df_economici.iterrows()):
                with st.container():
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.markdown(f"**{row['nome_pane']}**")
                    with col_b:
                        costo_kg = row['costo_totale_per_100kg'] / 100
                        st.markdown(f"**{fmt_euro(costo_kg, 2)}/kg**")
                    
                    # Progress bar relativa al costo massimo
                    costo_max = df_costi['costo_totale_per_100kg'].max()
                    progress_value = row['costo_totale_per_100kg'] / costo_max
                    
                    col_prog1, col_prog2 = st.columns([1, 4])
                    with col_prog1:
                        st.markdown(fmt_euro(row['costo_totale_per_100kg'], 0))
                    with col_prog2:
                        st.progress(progress_value, text=f"{progress_value*100:.0f}% del max")
                    
                    if idx < 4:
                        st.markdown("---")
            
            # Statistiche aggiuntive
            st.markdown("---")
            st.subheader("📊 Statistiche Rapide")
            
            st.metric(
                "Range Costi",
                f"{fmt_euro(analyzer.df_combinato['costo_totale_per_100kg'].min(), 0)} - {fmt_euro(analyzer.df_combinato['costo_totale_per_100kg'].max(), 0)}",
                help="Range costi per 100kg"
            )
            
            st.metric(
                "Deviazione Standard",
                fmt_euro(analyzer.df_combinato['costo_totale_per_100kg'].std(), 1),
                help="Variabilità dei costi"
            )
        
        # Stato magazzino migliorato
        st.markdown("---")
        st.subheader("📦 Stato Magazzino - Panoramica")
        
        # Crea grafico a barre per magazzino
        df_magazzino_viz = analyzer.df_magazzino.copy()
        df_magazzino_viz['percentuale_scorta'] = (df_magazzino_viz['quantita_kg'] / 
                                                 df_magazzino_viz['scorta_minima'] * 100)
        df_magazzino_viz = df_magazzino_viz.sort_values('quantita_kg', ascending=True)
        
        # Colori in base allo stato scorte
        colors = []
        stati = []
        for perc in df_magazzino_viz['percentuale_scorta']:
            if perc < 50:
                colors.append('#E74C3C')  # Rosso per critico
                stati.append('🔴 Critico')
            elif perc < 100:
                colors.append('#F39C12')  # Arancione per basso
                stati.append('🟠 Basso')
            elif perc < 150:
                colors.append('#3498DB')  # Blu per normale
                stati.append('🔵 Normale')
            else:
                colors.append('#2ECC71')  # Verde per buono
                stati.append('🟢 Buono')
        
        df_magazzino_viz['stato'] = stati
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=df_magazzino_viz['quantita_kg'],
            y=df_magazzino_viz['ingrediente'],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='rgba(0,0,0,0.2)', width=1)
            ),
            text=df_magazzino_viz.apply(
                lambda row: f"{row['quantita_kg']:.1f} kg ({row['percentuale_scorta']:.0f}%)",
                axis=1
            ),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                          'Quantità: %{x:.1f} kg<br>' +
                          'Scorta min: %{customdata[0]:.1f} kg<br>' +
                          'Percentuale: %{customdata[1]:.0f}%<br>' +
                          'Stato: %{customdata[2]}<extra></extra>',
            customdata=df_magazzino_viz[['scorta_minima', 'percentuale_scorta', 'stato']].values,
            name='Quantità Attuale'
        ))
        
        # Aggiungi linea per scorta minima (meno intrusivo)
        for idx, row in df_magazzino_viz.iterrows():
            fig2.add_shape(
                type="line",
                x0=row['scorta_minima'],
                x1=row['scorta_minima'],
                y0=idx-0.35,
                y1=idx+0.35,
                line=dict(color="rgba(255,0,0,0.4)", width=2.5, dash="dash"),
                opacity=0.7
            )
        
        fig2.update_layout(
            title='📦 Stato Magazzino Ingredienti - Confronto con Scorta Minima',
            xaxis_title='Quantità (kg) — Linea tratteggiata = Scorta Minima',
            yaxis_title='Ingrediente',
            height=520,
            showlegend=False,
            plot_bgcolor='rgba(240,240,240,0.3)',
            hovermode='closest',
            font=dict(size=11),
            margin=dict(l=200, r=100, t=60, b=60)
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Tabella magazzino con avvisi
        with st.expander("📋 Visualizza Dettaglio Completo Magazzino"):
            df_display = analyzer.df_magazzino.copy()
            df_display['Stato'] = np.where(
                df_display['quantita_kg'] < df_display['scorta_minima'],
                '⚠️ CRITICO',
                np.where(
                    df_display['quantita_kg'] < df_display['scorta_minima'] * 1.2,
                    '🔶 BASSO',
                    '✅ OK'
                )
            )
            
            # Calcola giorni di scorta (stima)
            df_display['Giorni Scorta'] = (df_display['quantita_kg'] / 
                                          df_display['scorta_minima'] * 30).round(1)
            
            # Formatta la data
            if 'data_aggiornamento' in df_display.columns:
                df_display['data_aggiornamento'] = pd.to_datetime(df_display['data_aggiornamento'])
            
            st.dataframe(
                df_display[['ingrediente', 'quantita_kg', 'scorta_minima', 
                           'Giorni Scorta', 'Stato', 'data_aggiornamento']],
                use_container_width=True,
                column_config={
                    "ingrediente": st.column_config.TextColumn(
                        "Ingrediente",
                        width="medium"
                    ),
                    "quantita_kg": st.column_config.NumberColumn(
                        "Quantità (kg)",
                        format="%.1f kg",
                        width="small"
                    ),
                    "scorta_minima": st.column_config.NumberColumn(
                        "Scorta Minima",
                        format="%.1f kg",
                        width="small"
                    ),
                    "Giorni Scorta": st.column_config.NumberColumn(
                        "Giorni Scorta",
                        format="%.1f giorni",
                        width="small",
                        help="Giorni stimati di scorta al consumo attuale"
                    ),
                    "Stato": st.column_config.TextColumn(
                        "Stato",
                        width="small"
                    ),
                    "data_aggiornamento": st.column_config.DatetimeColumn(
                        "Ultimo Aggiornamento",
                        format="DD/MM/YY",
                        width="small"
                    )
                }
            )
            
            # Pulsante per ordinare ingredienti bassi
            ingredienti_critici = df_display[df_display['Stato'] == '⚠️ CRITICO']['ingrediente'].tolist()
            ingredienti_bassi = df_display[df_display['Stato'] == '🔶 BASSO']['ingrediente'].tolist()
            
            if ingredienti_critici:
                st.error(f"**ATTENZIONE CRITICA:** {len(ingredienti_critici)} ingredienti CRITICI: {', '.join(ingredienti_critici)}")
                registra_log("ATTENZIONE", "Scorte critiche rilevate", f"Ingredienti: {', '.join(ingredienti_critici)}")
            
            if ingredienti_bassi:
                st.warning(f"**Attenzione:** {len(ingredienti_bassi)} ingredienti BASSO: {', '.join(ingredienti_bassi)}")
                registra_log("ATTENZIONE", "Scorte basse rilevate", f"Ingredienti: {', '.join(ingredienti_bassi)}")
    
    elif pagina == "💰 Analisi Costi":
        st.header("💰 Analisi Dettagliata Costi")
        registra_log("PAGINA", "Accesso Analisi Costi")
        
        # Statistiche rapide in alto
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            costo_medio = analyzer.df_combinato['costo_totale_per_100kg'].mean()
            st.metric(
                "💰 Costo Medio",
                fmt_euro(costo_medio, 2),
                help="Costo medio per 100kg di prodotto",
                delta="per 100kg"
            )
        
        with col_stats2:
            spread_cost = analyzer.df_combinato['costo_totale_per_100kg'].max() - analyzer.df_combinato['costo_totale_per_100kg'].min()
            st.metric(
                "📊 Variazione Costi",
                fmt_euro(spread_cost, 2),
                help="Differenza tra prodotto più costoso e più economico",
                delta_color="off"
            )
        
        with col_stats3:
            prop_ingredienti = (analyzer.df_combinato['costo_ingredienti_per_100kg'] / 
                              analyzer.df_combinato['costo_totale_per_100kg']).mean() * 100
            st.metric(
                "% Ingredienti",
                fmt_percentuale(prop_ingredienti, 1),
                help="Percentuale media del costo dedicata agli ingredienti"
            )
        
        with col_stats4:
            prodotti_analizzati = len(analyzer.df_combinato)
            st.metric(
                "📦 Prodotti",
                fmt_numero(prodotti_analizzati),
                help="Prodotti disponibili nell'analisi"
            )
        
        # Selezione prodotto per analisi dettagliata
        st.markdown("---")
        st.subheader("📊 Analisi Prodotto Specifico")
        
        # Invece di una semplice selectbox, crea una griglia di prodotti
        prodotti = analyzer.df_combinato['nome_pane'].tolist()
        
        col_sel1, col_sel2 = st.columns([2, 1])
        
        with col_sel1:
            prodotto_selezionato = st.selectbox(
                "Seleziona un prodotto per analisi dettagliata:",
                prodotti,
                index=0,
                help="Seleziona un prodotto per vedere il dettaglio dei costi",
                key="prodotto_selezione_dettaglio"
            )
        
        with col_sel2:
            # Mostra informazioni rapide del prodotto selezionato
            if prodotto_selezionato:
                prodotto_data = analyzer.df_combinato[
                    analyzer.df_combinato['nome_pane'] == prodotto_selezionato
                ].iloc[0]
                
                costo_kg = prodotto_data['costo_totale_per_100kg'] / 100
                st.info(f"**{fmt_euro(costo_kg, 2)}/kg**")
        
        if prodotto_selezionato:
            registra_log("ANALISI", f"Analisi costi prodotto: {prodotto_selezionato}")
            
            # Calcola costo dettagliato
            try:
                with st.spinner(f"Calcolando costi per {prodotto_selezionato}..."):
                    costo_dettaglio = analyzer.calcola_costo_totale_prodotto(prodotto_selezionato)
                    registra_log("CALCOLO", f"Costi calcolati per {prodotto_selezionato}", 
                               f"Totale: {fmt_euro(costo_dettaglio['costo_totale'], 2)}")
                
                # Metriche dettagliate con layout migliorato
                st.markdown("---")
                st.subheader("📈 Dettaglio Costi")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="Costo Ingredienti",
                        value=fmt_euro(costo_dettaglio['costo_ingredienti'], 2),
                        delta="per 100kg",
                        help="Costo totale degli ingredienti necessari per 100kg di prodotto"
                    )
                
                with col2:
                    st.metric(
                        label="Costo Produzione",
                        value=fmt_euro(costo_dettaglio['costo_produzione'], 2),
                        delta="per 100kg",
                        help="Costo delle fasi di produzione per 100kg di prodotto"
                    )
                
                with col3:
                    st.metric(
                        label="Costo Totale",
                        value=fmt_euro(costo_dettaglio['costo_totale'], 2),
                        delta=f"{fmt_euro(costo_dettaglio['costo_totale']/100, 2)}/kg",
                        help="Costo totale per 100kg di prodotto"
                    )
                
                with col4:
                    margine_produzione = (costo_dettaglio['costo_produzione'] / 
                                        costo_dettaglio['costo_totale'] * 100)
                    st.metric(
                        label="% Produzione",
                        value=fmt_percentuale(margine_produzione, 1),
                        help="Percentuale costo dedicata alla produzione"
                    )
                
                # Visualizzazione grafica migliorata
                st.markdown("---")
                st.subheader("📊 Visualizzazione Grafica")
                
                # Prima riga di grafici
                col_graph1, col_graph2 = st.columns(2)
                
                with col_graph1:
                    # Grafico a torta dei costi (semplificato)
                    labels = ['Ingredienti', 'Produzione']
                    values = [costo_dettaglio['costo_ingredienti'], costo_dettaglio['costo_produzione']]
                    
                    fig_torta = go.Figure(data=[go.Pie(
                        labels=labels, 
                        values=values,
                        hole=.4,
                        marker_colors=['#FF6B6B', '#4ECDC4'],
                        textinfo='label+percent',
                        texttemplate='<b>%{label}</b><br>%{percent:.1f}%',
                        textposition='auto',
                        hovertemplate='<b>%{label}</b><br>' +
                                      'Costo: €%{value:.2f}<br>' +
                                      'Percentuale: %{percent:.1f%}<extra></extra>',
                        pull=[0.1, 0]
                    )])
                    
                    fig_torta.update_layout(
                        title=f"💰 Composizione Costi - {prodotto_selezionato}",
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=11)
                        ),
                        height=380,
                        font=dict(size=12, family="Arial"),
                        paper_bgcolor='white'
                    )
                    
                    st.plotly_chart(fig_torta, use_container_width=True)
                
                with col_graph2:
                    # Grafico a barre ingredienti (solo top 8 se molti ingredienti)
                    if costo_dettaglio['ingredienti']:
                        df_ingredienti = pd.DataFrame(costo_dettaglio['ingredienti'])
                        
                        # Calcola percentuale sul totale COMPLETO degli ingredienti PRIMA del sort
                        totale_costo_ingredienti = df_ingredienti['costo_totale'].sum()
                        df_ingredienti['percentuale'] = (df_ingredienti['costo_totale'] / totale_costo_ingredienti * 100)
                        
                        # Ordina e prendi top 8 ingredienti per costo
                        df_ingredienti = df_ingredienti.sort_values('costo_totale', ascending=True).tail(8)
                        
                        fig_ingredienti = go.Figure()
                        
                        fig_ingredienti.add_trace(go.Bar(
                            y=df_ingredienti['nome'],
                            x=df_ingredienti['costo_totale'],
                            orientation='h',
                            name='Costo Ingrediente',
                            marker=dict(
                                color=df_ingredienti['costo_totale'],
                                colorscale='Viridis',
                                showscale=False
                            ),
                            text=df_ingredienti.apply(
                                lambda row: f"{fmt_euro(row['costo_totale'], 2)} ({row['percentuale']:.1f}%)",
                                axis=1
                            ),
                            textposition='auto',
                            hovertemplate='<b>%{y}</b><br>' +
                                          'Costo: €%{x:.2f}<br>' +
                                          'Percentuale: %{customdata[2]:.1f}%<br>' +
                                          'Quantità: %{customdata[0]:.3f}kg<br>Costo/kg: €%{customdata[1]:.2f}<extra></extra>',
                            customdata=df_ingredienti[['quantita_kg', 'costo_kg', 'percentuale']].values
                        ))
                        
                        fig_ingredienti.update_layout(
                            title="📦 Top 8 Ingredienti per Costo",
                            xaxis_title="Costo (€)",
                            yaxis_title="Ingrediente",
                            showlegend=False,
                            height=380,
                            plot_bgcolor='rgba(240,240,240,0.5)',
                            font=dict(size=11),
                            margin=dict(l=150, r=20, t=50, b=20)
                        )
                        
                        st.plotly_chart(fig_ingredienti, use_container_width=True)
                    else:
                        st.info("Nessun dato ingredienti disponibile")
                
                # Seconda riga: Tabella dettagliata con espansori
                st.markdown("---")
                st.subheader("📋 Dettaglio Completo")
                
                tab1, tab2, tab3 = st.tabs(["🗒️ Ingredienti", "⚙️ Fasi Produzione", "📊 Benchmark"])
                
                with tab1:
                    if costo_dettaglio['ingredienti']:
                        df_ing_tab = pd.DataFrame(costo_dettaglio['ingredienti'])
                        
                        # Calcola percentuale sul totale
                        df_ing_tab['percentuale'] = (df_ing_tab['costo_totale'] / 
                                                    df_ing_tab['costo_totale'].sum() * 100)
                        
                        # Ordina per costo
                        df_ing_tab = df_ing_tab.sort_values('costo_totale', ascending=False)
                        
                        st.dataframe(
                            df_ing_tab,
                            use_container_width=True,
                            column_config={
                                "nome": st.column_config.TextColumn(
                                    "Ingrediente",
                                    width="medium"
                                ),
                                "quantita_kg": st.column_config.NumberColumn(
                                    "Quantità",
                                    format="%.3f kg",
                                    help="Quantità necessaria per 100kg di prodotto",
                                    width="small"
                                ),
                                "costo_kg": st.column_config.NumberColumn(
                                    "Costo/kg",
                                    format="€%.2f",
                                    help="Costo al chilogrammo dell'ingrediente",
                                    width="small"
                                ),
                                "costo_totale": st.column_config.NumberColumn(
                                    "Costo Totale",
                                    format="€%.2f",
                                    help="Costo totale dell'ingrediente per 100kg di prodotto",
                                    width="small"
                                ),
                                "percentuale": st.column_config.NumberColumn(
                                    "% Totale",
                                    format="%.1f%%",
                                    help="Percentuale sul costo totale ingredienti",
                                    width="small"
                                )
                            }
                        )
                        
                        # Sommario ingredienti
                        st.markdown("---")
                        col_sum1, col_sum2, col_sum3 = st.columns(3)
                        
                        with col_sum1:
                            st.metric("N° Ingredienti", len(df_ing_tab))
                        
                        with col_sum2:
                            ingrediente_costoso = df_ing_tab.iloc[0]['nome']
                            st.metric("Ingrediente più Costoso", ingrediente_costoso[:20])
                        
                        with col_sum3:
                            costo_max_ing = df_ing_tab['costo_totale'].max()
                            st.metric("Costo Max Ingrediente", fmt_euro(costo_max_ing, 2))
                    
                    else:
                        st.info("Nessun dato ingredienti disponibile")
                
                with tab2:
                    if costo_dettaglio.get('fasi'):
                        try:
                            # Converti in DataFrame
                            df_fasi_tab = pd.DataFrame(costo_dettaglio['fasi'])
                            
                            # Debug: mostra la struttura dei dati
                            st.write("Debug - Struttura dati fasi:")
                            st.write(df_fasi_tab.columns.tolist())
                            st.write(df_fasi_tab.head())
                            
                            # Verifica che ci siano dati validi
                            if not df_fasi_tab.empty and len(df_fasi_tab) > 0:
                                # Calcola percentuale se abbiamo costi totali
                                if 'costo_totale' in df_fasi_tab.columns and df_fasi_tab['costo_totale'].sum() > 0:
                                    df_fasi_tab['percentuale'] = (df_fasi_tab['costo_totale'] / 
                                                                 df_fasi_tab['costo_totale'].sum() * 100).round(1)
                                
                                # Controlla colonne disponibili
                                colonne_disponibili = df_fasi_tab.columns.tolist()
                                colonne_visualizzare = []
                                column_config = {}
                                
                                # Gestisci nome della fase
                                if 'nome' in colonne_disponibili:
                                    colonne_visualizzare.append('nome')
                                    column_config['nome'] = st.column_config.TextColumn(
                                        "Fase di Produzione",
                                        width="medium"
                                    )
                                
                                # Gestisci durata
                                if 'durata_ore' in colonne_disponibili:
                                    colonne_visualizzare.append('durata_ore')
                                    column_config['durata_ore'] = st.column_config.NumberColumn(
                                        "Durata",
                                        format="%.2f ore",
                                        help="Durata della fase in ore",
                                        width="small"
                                    )
                                elif 'tempo_min' in colonne_disponibili:
                                    df_fasi_tab['durata_ore'] = df_fasi_tab['tempo_min'] / 60
                                    colonne_visualizzare.append('durata_ore')
                                    column_config['durata_ore'] = st.column_config.NumberColumn(
                                        "Durata",
                                        format="%.2f ore",
                                        help="Durata della fase in ore",
                                        width="small"
                                    )
                                
                                # Gestisci costo orario
                                if 'costo_orario' in colonne_disponibili:
                                    colonne_visualizzare.append('costo_orario')
                                    column_config['costo_orario'] = st.column_config.NumberColumn(
                                        "Costo/ora",
                                        format="€%.2f",
                                        help="Costo orario della fase",
                                        width="small"
                                    )
                                
                                # Gestisci costo totale
                                if 'costo_totale' in colonne_disponibili:
                                    colonne_visualizzare.append('costo_totale')
                                    column_config['costo_totale'] = st.column_config.NumberColumn(
                                        "Costo Fase",
                                        format="€%.2f",
                                        help="Costo totale della fase",
                                        width="small"
                                    )
                                
                                # Gestisci percentuale se esiste
                                if 'percentuale' in df_fasi_tab.columns:
                                    colonne_visualizzare.append('percentuale')
                                    column_config['percentuale'] = st.column_config.NumberColumn(
                                        "% Produzione",
                                        format="%.1f%%",
                                        help="Percentuale sul costo totale produzione",
                                        width="small"
                                    )
                                
                                # Mostra tabella solo se ci sono colonne da mostrare
                                if colonne_visualizzare:
                                    st.dataframe(
                                        df_fasi_tab[colonne_visualizzare],
                                        use_container_width=True,
                                        column_config=column_config,
                                        hide_index=True
                                    )
                                    
                                    # Grafico timeline fasi se abbiamo dati di durata
                                    if 'durata_ore' in colonne_visualizzare and 'nome' in colonne_visualizzare:
                                        fig_timeline = px.bar(
                                            df_fasi_tab,
                                            x='nome',
                                            y='durata_ore',
                                            title='Durata Fasi di Produzione',
                                            labels={'nome': 'Fase', 'durata_ore': 'Durata (ore)'},
                                            text='durata_ore',
                                            color='costo_totale' if 'costo_totale' in df_fasi_tab.columns else None
                                        )
                                        
                                        fig_timeline.update_traces(
                                            texttemplate='%{y:.1f}h',
                                            textposition='outside'
                                        )
                                        fig_timeline.update_layout(
                                            height=350,
                                            xaxis_tickangle=-45 if len(df_fasi_tab) > 3 else 0
                                        )
                                        
                                        st.plotly_chart(fig_timeline, use_container_width=True)
                                        
                                        # Sommario statistiche fasi
                                        st.markdown("---")
                                        col_fasi1, col_fasi2, col_fasi3 = st.columns(3)
                                        
                                        with col_fasi1:
                                            fase_lunga = df_fasi_tab.loc[df_fasi_tab['durata_ore'].idxmax(), 'nome']
                                            st.metric("Fase più Lunga", fase_lunga[:20])
                                        
                                        with col_fasi2:
                                            tot_durata = df_fasi_tab['durata_ore'].sum()
                                            st.metric("Durata Totale", f"{tot_durata:.1f} ore")
                                        
                                        with col_fasi3:
                                            if 'costo_totale' in df_fasi_tab.columns:
                                                tot_costo_fasi = df_fasi_tab['costo_totale'].sum()
                                                st.metric("Costo Fasi", fmt_euro(tot_costo_fasi, 2))
                                else:
                                    st.warning("Nessuna colonna valida trovata nei dati delle fasi")
                            else:
                                st.info("Nessun dato valido disponibile per le fasi di produzione")
                                
                        except Exception as e:
                            st.error(f"Errore nell'elaborazione delle fasi: {str(e)}")
                            # Mostra i dati grezzi per debug
                            st.write("Dati grezzi fasi:", costo_dettaglio['fasi'])
                    else:
                        st.info("Nessun dato fasi produzione disponibile per questo prodotto")
                
                with tab3:
                    # Confronto con altri prodotti
                    st.write("**Confronto con altri prodotti:**")
                    
                    # Seleziona prodotti per confronto
                    prodotti_confronto = st.multiselect(
                        "Seleziona prodotti da confrontare:",
                        [p for p in prodotti if p != prodotto_selezionato],
                        default=[p for p in prodotti if p != prodotto_selezionato][:3],
                        help="Seleziona prodotti per confrontare i costi",
                        key="prodotti_confronto"
                    )
                    
                    if prodotti_confronto:
                        dati_confronto = []
                        
                        # Aggiungi prodotto selezionato
                        dati_confronto.append({
                            'Prodotto': prodotto_selezionato,
                            'Costo Totale': costo_dettaglio['costo_totale'],
                            'Costo Ingredienti': costo_dettaglio['costo_ingredienti'],
                            'Costo Produzione': costo_dettaglio['costo_produzione'],
                            'Tipo': 'Selezionato'
                        })
                        
                        # Aggiungi prodotti di confronto
                        for prodotto in prodotti_confronto:
                            try:
                                costo = analyzer.calcola_costo_totale_prodotto(prodotto)
                                dati_confronto.append({
                                    'Prodotto': prodotto,
                                    'Costo Totale': costo['costo_totale'],
                                    'Costo Ingredienti': costo['costo_ingredienti'],
                                    'Costo Produzione': costo['costo_produzione'],
                                    'Tipo': 'Confronto'
                                })
                            except Exception as e:
                                st.error(f"Errore nel calcolo per {prodotto}: {str(e)}")
                                continue
                        
                        if len(dati_confronto) > 1:
                            df_confronto = pd.DataFrame(dati_confronto)
                            
                            # Grafico a barre raggruppate
                            fig_confronto = go.Figure()
                            
                            # Aggiungi barre per costo ingredienti
                            fig_confronto.add_trace(go.Bar(
                                x=df_confronto['Prodotto'],
                                y=df_confronto['Costo Ingredienti'],
                                name='Ingredienti',
                                marker_color='#FF6B6B',
                                text=df_confronto['Costo Ingredienti'].apply(lambda x: fmt_euro(x, 1)),
                                textposition='inside'
                            ))
                            
                            # Aggiungi barre per costo produzione
                            fig_confronto.add_trace(go.Bar(
                                x=df_confronto['Prodotto'],
                                y=df_confronto['Costo Produzione'],
                                name='Produzione',
                                marker_color='#4ECDC4',
                                text=df_confronto['Costo Produzione'].apply(lambda x: fmt_euro(x, 1)),
                                textposition='inside'
                            ))
                            
                            fig_confronto.update_layout(
                                title='Confronto Dettagliato Costi (per 100kg)',
                                xaxis_title='Prodotto',
                                yaxis_title='Costo (€)',
                                barmode='stack',
                                height=400,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                            
                            st.plotly_chart(fig_confronto, use_container_width=True)
                            
                            # Tabella comparativa
                            st.dataframe(
                                df_confronto,
                                use_container_width=True,
                                column_config={
                                    "Prodotto": "Prodotto",
                                    "Costo Totale": st.column_config.NumberColumn(
                                        "Costo Totale",
                                        format="€%.2f"
                                    ),
                                    "Costo Ingredienti": st.column_config.NumberColumn(
                                        "Ingredienti",
                                        format="€%.2f"
                                    ),
                                    "Costo Produzione": st.column_config.NumberColumn(
                                        "Produzione",
                                        format="€%.2f"
                                    ),
                                    "Tipo": "Tipo"
                                }
                            )
                
                # Analisi costi globale
                st.markdown("---")
                st.subheader("📈 Analisi Costi Globale - Tutti i Prodotti")
                
                if st.button("🔄 Genera Analisi Costi Completa", type="primary", key="analisi_globale_btn"):
                    registra_log("ANALISI", "Avvio analisi costi globale")
                    with st.spinner("Analizzando tutti i prodotti..."):
                        try:
                            # Usa la funzione analisi_costi_globale_migliorata()
                            analisi_data = analisi_costi_globale_migliorata()
                            
                            if analisi_data:
                                st.session_state.analisi_costi_data = analisi_data
                                registra_log("SUCCESSO", "Analisi costi globale completata")
                                
                                # Layout a tre colonne per le metriche principali
                                col_glob1, col_glob2, col_glob3 = st.columns(3)
                                
                                with col_glob1:
                                    costo_max = analisi_data["top_10_costosi"]["Costo per kg (€)"].max()
                                    st.metric("💰 Prodotto più Costoso", 
                                             f"{fmt_euro(costo_max, 2)}/kg",
                                             help="Costo per kg del prodotto più costoso")
                                
                                with col_glob2:
                                    costo_min = analisi_data["top_10_economici"]["Costo per kg (€)"].min()
                                    st.metric("💸 Prodotto più Economico", 
                                             f"{fmt_euro(costo_min, 2)}/kg",
                                             help="Costo per kg del prodotto più economico")
                                
                                with col_glob3:
                                    rapporto_costoso_economico = costo_max / costo_min if costo_min > 0 else 0
                                    st.metric("📊 Rapporto Costi", 
                                             f"{rapporto_costoso_economico:.1f}x",
                                             help="Quanto è più costoso il prodotto più costoso",
                                             delta_color="inverse")
                                
                                # Sezione Top 10 Prodotti Costosi
                                st.markdown("---")
                                st.subheader("🏆 Top 10 Prodotti più Costosi")
                                
                                col_cost1, col_cost2 = st.columns([3, 2])
                                
                                with col_cost1:
                                    # Tabella con formattazione migliorata
                                    df_costosi = analisi_data["top_10_costosi"].copy()
                                    df_costosi['Posizione'] = range(1, len(df_costosi) + 1)
                                    
                                    st.dataframe(
                                        df_costosi,
                                        use_container_width=True,
                                        column_config={
                                            "Posizione": st.column_config.NumberColumn(
                                                "#",
                                                format="%d",
                                                width="small"
                                            ),
                                            "nome_pane": st.column_config.TextColumn(
                                                "Prodotto",
                                                width="large"
                                            ),
                                            "Costo per kg (€)": st.column_config.NumberColumn(
                                                "Costo/kg",
                                                format="€%.2f",
                                                help="Costo per chilogrammo",
                                                width="medium"
                                            )
                                        },
                                        hide_index=True
                                    )
                                
                                with col_cost2:
                                    # Grafico migliorato
                                    fig_costosi = analisi_data["fig_costosi"]
                                    fig_costosi.update_layout(
                                        height=400,
                                        showlegend=False,
                                        margin=dict(l=0, r=0, t=40, b=40)
                                    )
                                    st.plotly_chart(fig_costosi, use_container_width=True)
                                
                                # Sezione Top 10 Prodotti Economici
                                st.markdown("---")
                                st.subheader("💰 Top 10 Prodotti più Economici")
                                
                                col_econ1, col_econ2 = st.columns([3, 2])
                                
                                with col_econ1:
                                    df_economici = analisi_data["top_10_economici"].copy()
                                    df_economici['Posizione'] = range(1, len(df_economici) + 1)
                                    
                                    st.dataframe(
                                        df_economici,
                                        use_container_width=True,
                                        column_config={
                                            "Posizione": st.column_config.NumberColumn(
                                                "#",
                                                format="%d",
                                                width="small"
                                            ),
                                            "nome_pane": st.column_config.TextColumn(
                                                "Prodotto",
                                                width="large"
                                            ),
                                            "Costo per kg (€)": st.column_config.NumberColumn(
                                                "Costo/kg",
                                                format="€%.2f",
                                                help="Costo per chilogrammo",
                                                width="medium"
                                            )
                                        },
                                        hide_index=True
                                    )
                                
                                with col_econ2:
                                    fig_economici = analisi_data["fig_economici"]
                                    fig_economici.update_layout(
                                        height=400,
                                        showlegend=False,
                                        margin=dict(l=0, r=0, t=40, b=40)
                                    )
                                    st.plotly_chart(fig_economici, use_container_width=True)
                                
                                # Distribuzione Categorie
                                st.markdown("---")
                                st.subheader("📊 Distribuzione Prodotti per Fascia di Costo")
                                
                                col_cat1, col_cat2 = st.columns([2, 3])
                                
                                with col_cat1:
                                    # Tabella categorie
                                    if analisi_data["categoria_costi"] is not None:
                                        df_categorie = pd.DataFrame({
                                            'Categoria': analisi_data["categoria_costi"].index,
                                            'Numero Prodotti': analisi_data["categoria_costi"].values,
                                            'Percentuale': (analisi_data["categoria_costi"].values / 
                                                           analisi_data["categoria_costi"].sum() * 100)
                                        })
                                        
                                        st.dataframe(
                                            df_categorie,
                                            use_container_width=True,
                                            column_config={
                                                "Categoria": "Fascia Costo",
                                                "Numero Prodotti": st.column_config.NumberColumn(
                                                    "N° Prodotti",
                                                    format="%d"
                                                ),
                                                "Percentuale": st.column_config.NumberColumn(
                                                    "% Totale",
                                                    format="%.1f%%"
                                                )
                                            }
                                        )
                                
                                with col_cat2:
                                    # Grafico a torta migliorato
                                    fig_categorie = analisi_data["fig_categorie"]
                                    fig_categorie.update_layout(
                                        height=400,
                                        showlegend=True,
                                        legend=dict(
                                            orientation="h",
                                            yanchor="bottom",
                                            y=-0.3,
                                            xanchor="center",
                                            x=0.5
                                        ),
                                        margin=dict(l=0, r=0, t=40, b=80)
                                    )
                                    st.plotly_chart(fig_categorie, use_container_width=True)
                                
                                # Statistiche aggiuntive in griglia
                                st.markdown("---")
                                st.subheader("📈 Statistiche Riepilogative")
                                
                                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                
                                with col_stat1:
                                    media_costo = analisi_data["statistiche"]["media_costo_kg"]
                                    st.metric("Media Costi", f"{fmt_euro(media_costo, 2)}/kg")
                                
                                with col_stat2:
                                    dev_std = analisi_data["statistiche"]["std_costo_kg"]
                                    st.metric("Deviazione Standard", fmt_euro(dev_std, 2))
                                
                                with col_stat3:
                                    if analisi_data["categoria_costi"] is not None:
                                        cat_piu_numerosa = analisi_data["categoria_costi"].idxmax()
                                        st.metric("Categoria Maggioritaria", cat_piu_numerosa)
                                
                                with col_stat4:
                                    prodotti_analizzati = len(analisi_data["top_10_costosi"]) + len(analisi_data["top_10_economici"])
                                    st.metric("Prodotti Analizzati", prodotti_analizzati)
                                
                                # Visualizzazioni aggiuntive
                                st.markdown("---")
                                st.subheader("📊 Visualizzazioni Avanzate")
                                
                                # Distribuzione costi completa
                                st.plotly_chart(analisi_data["fig_distribuzione"], use_container_width=True)
                                
                                # Correlazione ingredienti vs produzione
                                st.plotly_chart(analisi_data["fig_correlazione"], use_container_width=True)
                                
                        except Exception as e:
                            registra_log("ERRORE", "Errore analisi costi globale", str(e))
                            st.error(f"Errore nella generazione dell'analisi: {str(e)}")
                
                # Se l'analisi è già stata generata, mostra un pulsante per visualizzarla
                elif 'analisi_costi_data' in st.session_state and st.session_state.analisi_costi_data:
                    st.info("📊 Analisi costi globale già disponibile")
                    
                    if st.button("👁️ Mostra Analisi Precedente", key="show_previous_analysis"):
                        analisi_data = st.session_state.analisi_costi_data
                        
                        # Mostra metriche rapide
                        col_prev1, col_prev2 = st.columns(2)
                        
                        with col_prev1:
                            costo_max = analisi_data["top_10_costosi"]["Costo per kg (€)"].max()
                            st.metric("Costo Massimo", f"{fmt_euro(costo_max, 2)}/kg")
                        
                        with col_prev2:
                            costo_min = analisi_data["top_10_economici"]["Costo per kg (€)"].min()
                            st.metric("Costo Minimo", f"{fmt_euro(costo_min, 2)}/kg")
                        
                        # Mostra grafici principali
                        st.plotly_chart(analisi_data["fig_costosi"], use_container_width=True)
                        st.plotly_chart(analisi_data["fig_economici"], use_container_width=True)
            
            except Exception as e:
                registra_log("ERRORE", f"Errore calcolo costi prodotto {prodotto_selezionato}", str(e))
                st.error(f"Errore nel calcolo del costo: {str(e)}")
                
                # Mostra dati grezzi in caso di errore
                with st.expander("🔄 Mostra Dati Grezzi per Debug"):
                    prodotto_data = analyzer.df_combinato[
                        analyzer.df_combinato['nome_pane'] == prodotto_selezionato
                    ]
                    st.write(prodotto_data)
    
    elif pagina == "📦 Gestione Magazzino":
        # [Mantieni la stessa implementazione della gestione magazzino]
        st.header("📦 Gestione Magazzino")
        registra_log("PAGINA", "Accesso Gestione Magazzino")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Stato Magazzino", 
            "📝 Verifica Disponibilità", 
            "🔄 Rifornimento", 
            "📋 Log Movimenti"
        ])
        
        with tab1:
            st.subheader("Stato Attuale Magazzino")
            registra_log("MAGAZZINO", "Visualizzazione stato magazzino")
            
            # Metriche magazzino
            col1, col2, col3 = st.columns(3)
            
            with col1:
                valore_totale = (analyzer.df_magazzino['quantita_kg'] * 10).sum()
                st.metric(
                    label="Valore Totale Scorte",
                    value=fmt_euro(valore_totale, 0),
                    delta="Valore approssimativo",
                    help="Valore approssimativo delle scorte in magazzino"
                )
            
            with col2:
                ingredienti_totali = len(analyzer.df_magazzino)
                st.metric(
                    label="Ingredienti Registrati",
                    value=ingredienti_totali
                )
            
            with col3:
                scorte_basse = sum(analyzer.df_magazzino['quantita_kg'] < 
                                 analyzer.df_magazzino['scorta_minima'])
                st.metric(
                    label="Ingredienti sotto Scorta Minima",
                    value=scorte_basse,
                    delta_color="inverse",
                    help="Numero di ingredienti sotto la scorta minima di sicurezza"
                )
            
            # Visualizzazione magazzino
            st.write("**Inventario Magazzino:**")
            
            # Opzioni filtro
            col_filtro1, col_filtro2 = st.columns(2)
            
            with col_filtro1:
                mostra_solo_basse = st.checkbox(
                    "Mostra solo scorte basse",
                    value=st.session_state.filter_stock_low
                )
                st.session_state.filter_stock_low = mostra_solo_basse
            
            with col_filtro2:
                ordina_per = st.selectbox(
                    "Ordina per:",
                    ["Quantità (decrescente)", "Quantità (crescente)", "Nome", "Scorta Minima"],
                    index=0
                )
            
            # Applica filtri
            df_magazzino_viz = analyzer.df_magazzino.copy()
            
            if mostra_solo_basse:
                df_magazzino_viz = df_magazzino_viz[
                    df_magazzino_viz['quantita_kg'] < df_magazzino_viz['scorta_minima']
                ]
                registra_log("FILTRO", "Applicato filtro scorte basse")
            
            if ordina_per == "Quantità (decrescente)":
                df_magazzino_viz = df_magazzino_viz.sort_values('quantita_kg', ascending=False)
            elif ordina_per == "Quantità (crescente)":
                df_magazzino_viz = df_magazzino_viz.sort_values('quantita_kg', ascending=True)
            elif ordina_per == "Scorta Minima":
                df_magazzino_viz = df_magazzino_viz.sort_values('scorta_minima', ascending=False)
            else:
                df_magazzino_viz = df_magazzino_viz.sort_values('ingrediente')
            
            # Mostra dataframe con colorazione
            def color_scorte(row):
                if row['quantita_kg'] < row['scorta_minima']:
                    return ['background-color: #FFCCCC'] * len(row)
                elif row['quantita_kg'] < row['scorta_minima'] * 1.5:
                    return ['background-color: #FFE5CC'] * len(row)
                else:
                    return [''] * len(row)
            
            if not df_magazzino_viz.empty:
                styled_df = df_magazzino_viz.style.apply(
                    color_scorte, 
                    axis=1
                )
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    column_config={
                        "ingrediente": "Ingrediente",
                        "quantita_kg": st.column_config.NumberColumn(
                            "Quantità (kg)",
                            help="Quantità attuale in magazzino",
                            format="%.2f kg"
                        ),
                        "scorta_minima": st.column_config.NumberColumn(
                            "Scorta Minima (kg)",
                            help="Livello minimo di sicurezza",
                            format="%.2f kg"
                        ),
                        "data_aggiornamento": "Ultimo Aggiornamento"
                    },
                    hide_index=True
                )
                
                # Grafico a barre
                fig = px.bar(
                    df_magazzino_viz,
                    x='ingrediente',
                    y='quantita_kg',
                    title='Quantità Ingredienti in Magazzino',
                    labels={'quantita_kg': 'Quantità (kg)', 'ingrediente': 'Ingrediente'},
                    color='quantita_kg',
                    color_continuous_scale='Viridis'
                )
                
                # Aggiungi linea scorta minima
                fig.add_trace(go.Scatter(
                    x=df_magazzino_viz['ingrediente'],
                    y=df_magazzino_viz['scorta_minima'],
                    mode='lines+markers',
                    name='Scorta Minima',
                    line=dict(color='red', dash='dash', width=2),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessun ingrediente corrisponde ai filtri selezionati")
        
        with tab2:
            st.subheader("Verifica Disponibilità per Produzione")
            
            col_sel, col_qta = st.columns(2)
            
            with col_sel:
                prodotto = st.selectbox(
                    "Seleziona prodotto:",
                    analyzer.df_combinato['nome_pane'].tolist(),
                    key="verifica_prodotto"
                )
            
            with col_qta:
                quantita = st.number_input(
                    "Quantità da produrre (kg):",
                    min_value=0.1,
                    max_value=10000.0,
                    value=100.0,
                    step=10.0,
                    key="verifica_quantita"
                )
            
            if st.button("🔍 Verifica Disponibilità", type="primary"):
                registra_log("VERIFICA", f"Verifica disponibilità per {quantita}kg di {prodotto}")
                with st.spinner("Analizzando magazzino..."):
                    try:
                        disponibilita = analyzer.verifica_disponibilita_magazzino(prodotto, quantita)
                        
                        if disponibilita['disponibile']:
                            st.success("✅ **Tutti gli ingredienti sono disponibili!**")
                            registra_log("SUCCESSO", f"Disponibilità confermata per {quantita}kg di {prodotto}")
                            
                            # Mostra dettaglio
                            with st.expander("📋 Visualizza Dettaglio Ingredienti"):
                                df_disp = pd.DataFrame(disponibilita['ingredienti'])
                                
                                # Calcola percentuali
                                df_disp['percentuale_utilizzo'] = (
                                    df_disp['quantita_richiesta_kg'] / df_disp['disponibile_kg'] * 100
                                )
                                
                                st.dataframe(
                                    df_disp[['nome', 'quantita_richiesta_kg', 'disponibile_kg', 
                                            'percentuale_utilizzo', 'sufficiente']],
                                    use_container_width=True,
                                    column_config={
                                        "nome": "Ingrediente",
                                        "quantita_richiesta_kg": st.column_config.NumberColumn(
                                            "Richiesto (kg)",
                                            format="%.3f kg"
                                        ),
                                        "disponibile_kg": st.column_config.NumberColumn(
                                            "Disponibile (kg)",
                                            format="%.3f kg"
                                        ),
                                        "percentuale_utilizzo": st.column_config.NumberColumn(
                                            "Utilizzo %",
                                            format="%.1f%%"
                                        ),
                                        "sufficiente": "Disponibile"
                                    }
                                )
                            
                            # Pulsante per procedere con produzione
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if st.button("🔄 Conferma Produzione", type="primary"):
                                    registra_log("PRODUZIONE", f"Conferma produzione {quantita}kg di {prodotto}")
                                    # Calcola utilizzo ingredienti
                                    utilizzo = {}
                                    for ingrediente in disponibilita['ingredienti']:
                                        utilizzo[ingrediente['nome']] = ingrediente['quantita_richiesta_kg']
                                    
                                    # Aggiorna magazzino
                                    if analyzer.aggiorna_magazzino(utilizzo, f"Produzione {prodotto}"):
                                        registra_log("SUCCESSO", f"Magazzino aggiornato per produzione {prodotto}")
                                        st.success("✅ Magazzino aggiornato con successo!")
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        registra_log("ERRORE", f"Errore aggiornamento magazzino per {prodotto}")
                                        st.error("❌ Errore nell'aggiornamento del magazzino")
                            
                            with col_btn2:
                                if st.button("📋 Genera Ordine di Produzione"):
                                    registra_log("ORDINE", f"Generazione ordine produzione per {prodotto}")
                                    st.info("Funzionalità ordine di produzione in sviluppo")
                        
                        else:
                            st.error("❌ **Ingredienti insufficienti per la produzione**")
                            registra_log("ATTENZIONE", f"Disponibilità insufficiente per {quantita}kg di {prodotto}")
                            
                            # Mostra ingredienti mancanti
                            st.write("**Ingredienti insufficienti:**")
                            
                            if disponibilita.get('ingredienti_mancanti'):
                                df_mancanti = pd.DataFrame(disponibilita['ingredienti_mancanti'])
                                
                                for _, row in df_mancanti.iterrows():
                                    col_warn1, col_warn2 = st.columns([2, 1])
                                    with col_warn1:
                                        st.warning(f"**{row['ingrediente']}**")
                                    with col_warn2:
                                        st.error(f"Mancano {row['mancante_kg']:.2f} kg")
                            
                            # Suggerimenti per quantità ridotta
                            st.write("**💡 Suggerimenti:**")
                            
                            col_sugg1, col_sugg2 = st.columns(2)
                            
                            with col_sugg1:
                                quantita_ridotta = quantita * 0.5
                                if st.button(f"Verifica per {quantita_ridotta:.1f} kg"):
                                    registra_log("VERIFICA", f"Verifica quantità ridotta: {quantita_ridotta}kg di {prodotto}")
                                    disponibilita_ridotta = analyzer.verifica_disponibilita_magazzino(
                                        prodotto, quantita_ridotta
                                    )
                                    
                                    if disponibilita_ridotta['disponibile']:
                                        registra_log("SUCCESSO", f"Disponibile {quantita_ridotta}kg ({quantita_ridotta/quantita*100:.0f}%)")
                                        st.success(
                                            f"✅ Disponibile per {quantita_ridotta:.1f} kg "
                                            f"({quantita_ridotta/quantita*100:.0f}% della quantità richiesta)"
                                        )
                                    else:
                                        registra_log("ATTENZIONE", f"Ancora insufficiente a {quantita_ridotta}kg")
                                        st.error("Ancora insufficiente")
                            
                            with col_sugg2:
                                if st.button("📋 Elenco ingredienti da ordinare"):
                                    registra_log("ELENCO", "Generazione elenco ingredienti da ordinare")
                                    if disponibilita.get('ingredienti_mancanti'):
                                        df_ordine = pd.DataFrame(disponibilita['ingredienti_mancanti'])
                                        st.dataframe(
                                            df_ordine[['ingrediente', 'mancante_kg']],
                                            use_container_width=True
                                        )
                    
                    except Exception as e:
                        registra_log("ERRORE", f"Errore verifica disponibilità", str(e))
                        st.error(f"Errore nella verifica disponibilità: {str(e)}")
        
        with tab3:
            st.subheader("Rifornimento Magazzino")
            registra_log("RIFORNIMENTO", "Accesso modulo rifornimento")
            
            st.info("Aggiungi ingredienti al magazzino tramite rifornimento.")
            
            # Form per rifornimento singolo
            with st.form("form_rifornimento_singolo"):
                st.write("**Rifornimento Singolo Ingrediente**")
                
                col_ing, col_qta = st.columns(2)
                
                with col_ing:
                    ingrediente = st.selectbox(
                        "Ingrediente:",
                        analyzer.df_magazzino['ingrediente'].tolist(),
                        key="rifornimento_ingrediente"
                    )
                
                with col_qta:
                    quantita = st.number_input(
                        "Quantità (kg):",
                        min_value=0.1,
                        max_value=10000.0,
                        value=100.0,
                        step=10.0,
                        key="rifornimento_quantita"
                    )
                
                fornitore = st.text_input("Fornitore:", value="Fornitore standard", 
                                         key="rifornimento_fornitore")
                
                col_sub1, col_sub2 = st.columns(2)
                
                with col_sub1:
                    submitted = st.form_submit_button("➕ Aggiungi Rifornimento", type="primary")
                
                with col_sub2:
                    st.form_submit_button("🔄 Reset")
                
                if submitted:
                    rifornimento = [{'ingrediente': ingrediente, 'quantita_kg': quantita}]
                    
                    try:
                        registra_log("RIFORNIMENTO", f"Aggiunta {quantita}kg di {ingrediente}", f"Fornitore: {fornitore}")
                        if analyzer.rifornisci_magazzino(rifornimento, fornitore):
                            registra_log("SUCCESSO", f"Rifornimento completato: {quantita}kg di {ingrediente}")
                            st.success(f"✅ {quantita} kg di {ingrediente} aggiunti al magazzino!")
                            st.rerun()
                        else:
                            registra_log("ERRORE", "Errore aggiornamento magazzino")
                            st.error("❌ Errore nell'aggiornamento del magazzino")
                    except Exception as e:
                        registra_log("ERRORE", "Errore rifornimento", str(e))
                        st.error(f"Errore: {str(e)}")
            
            st.markdown("---")
            st.subheader("Rifornimento Multiplo")
            
            st.write("Aggiungi più ingredienti contemporaneamente:")
            
            # Widget per rifornimento multiplo
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                nuovo_ingrediente = st.selectbox(
                    "Nuovo ingrediente:",
                    analyzer.df_magazzino['ingrediente'].tolist(),
                    key="nuovo_ing"
                )
            
            with col2:
                nuova_quantita = st.number_input(
                    "Quantità (kg):",
                    min_value=0.1,
                    max_value=10000.0,
                    value=50.0,
                    step=10.0,
                    key="nuova_qta"
                )
            
            with col3:
                if st.button("➕ Aggiungi alla lista", key="aggiungi_rifornimento"):
                    st.session_state.rifornimenti.append({
                        'ingrediente': nuovo_ingrediente,
                        'quantita_kg': nuova_quantita
                    })
                    registra_log("RIFORNIMENTO", f"Aggiunto alla lista: {nuova_quantita}kg di {nuovo_ingrediente}")
            
            # Mostra lista rifornimenti
            if st.session_state.rifornimenti:
                st.write(f"**Rifornimenti da confermare ({len(st.session_state.rifornimenti)}):**")
                
                df_rifornimenti = pd.DataFrame(st.session_state.rifornimenti)
                st.dataframe(
                    df_rifornimenti,
                    use_container_width=True,
                    column_config={
                        "ingrediente": "Ingrediente",
                        "quantita_kg": st.column_config.NumberColumn(
                            "Quantità (kg)",
                            format="%.2f kg"
                        )
                    }
                )
                
                # Calcola totale
                totale_kg = df_rifornimenti['quantita_kg'].sum()
                st.info(f"**Totale:** {totale_kg:.2f} kg")
                
                fornitore_multiplo = st.text_input(
                    "Fornitore per tutti gli ingredienti:",
                    value="Fornitore standard",
                    key="fornitore_multiplo"
                )
                
                col_conf, col_canc = st.columns(2)
                
                with col_conf:
                    if st.button("✅ Conferma Tutti i Rifornimenti", type="primary"):
                        try:
                            registra_log("RIFORNIMENTO", f"Conferma rifornimenti multipli ({len(st.session_state.rifornimenti)} ingredienti)", f"Totale: {totale_kg}kg")
                            if analyzer.rifornisci_magazzino(
                                st.session_state.rifornimenti, 
                                fornitore_multiplo
                            ):
                                registra_log("SUCCESSO", "Rifornimenti multipli completati")
                                st.success(f"✅ {len(st.session_state.rifornimenti)} rifornimenti aggiunti!")
                                st.session_state.rifornimenti = []
                                st.rerun()
                            else:
                                registra_log("ERRORE", "Errore aggiornamento magazzino multiplo")
                                st.error("❌ Errore nell'aggiornamento del magazzino")
                        except Exception as e:
                            registra_log("ERRORE", "Errore rifornimento multiplo", str(e))
                            st.error(f"Errore: {str(e)}")
                
                with col_canc:
                    if st.button("🗑️ Cancella Tutti"):
                        registra_log("CANCELLAZIONE", "Cancellati tutti i rifornimenti in lista")
                        st.session_state.rifornimenti = []
                        st.rerun()
            else:
                st.info("Nessun rifornimento in lista. Aggiungi ingredienti dalla sezione sopra.")
        
        with tab4:
            st.subheader("📋 Log Movimenti Magazzino")
            registra_log("LOG", "Accesso log movimenti magazzino")
            
            # Mostra anche i log dell'applicazione
            st.write("**Log Movimenti Applicazione:**")
            
            if 'log_movimenti' in st.session_state and st.session_state.log_movimenti:
                # Crea DataFrame dai log
                df_app_log = pd.DataFrame(st.session_state.log_movimenti)
                
                # Filtri per i log
                col_filtro1, col_filtro2 = st.columns(2)
                
                with col_filtro1:
                    tipi_log = df_app_log['tipo'].unique().tolist()
                    tipo_filtro = st.multiselect("Filtra per tipo:", tipi_log, default=tipi_log)
                
                with col_filtro2:
                    cerca_testo = st.text_input("Cerca nel log:", "")
                
                # Applica filtri
                df_filtrato = df_app_log.copy()
                
                if tipo_filtro:
                    df_filtrato = df_filtrato[df_filtrato['tipo'].isin(tipo_filtro)]
                
                if cerca_testo:
                    df_filtrato = df_filtrato[
                        df_filtrato['descrizione'].str.contains(cerca_testo, case=False, na=False) |
                        df_filtrato['dettagli'].str.contains(cerca_testo, case=False, na=False)
                    ]
                
                # Ordina per data
                df_filtrato = df_filtrato.sort_values('timestamp', ascending=False)
                
                # Mostra tabella log
                st.dataframe(
                    df_filtrato,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": st.column_config.TextColumn(
                            "Data/Ora",
                            width="small"
                        ),
                        "tipo": st.column_config.TextColumn(
                            "Tipo",
                            width="small"
                        ),
                        "descrizione": st.column_config.TextColumn(
                            "Descrizione",
                            width="medium"
                        ),
                        "dettagli": st.column_config.TextColumn(
                            "Dettagli",
                            width="large"
                        )
                    }
                )
                
                # Statistiche log
                st.subheader("📊 Statistiche Log")
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Log Totali", len(df_app_log))
                
                with col_stat2:
                    successi = len(df_app_log[df_app_log['tipo'] == 'SUCCESSO'])
                    st.metric("Successi", successi)
                
                with col_stat3:
                    errori = len(df_app_log[df_app_log['tipo'] == 'ERRORE'])
                    st.metric("Errori", errori)
                
                # Pulsanti azione log
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("📥 Esporta Log", key="export_app_log"):
                        csv = df_app_log.to_csv(index=False)
                        st.download_button(
                            label="Scarica CSV",
                            data=csv,
                            file_name=f"log_applicazione_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            key="download_app_log"
                        )
                        registra_log("ESPORTAZIONE", "Esportazione log applicazione")
                
                with col_btn2:
                    if st.button("🗑️ Pulisci Log", type="secondary"):
                        st.session_state.log_movimenti = []
                        registra_log("PULIZIA", "Log applicazione puliti")
                        st.success("Log puliti!")
                        st.rerun()
                
                with col_btn3:
                    if st.button("🔄 Aggiorna", key="refresh_log"):
                        st.rerun()
            else:
                st.info("Nessun log disponibile nell'applicazione.")
            
            st.markdown("---")
            st.subheader("📋 Log Movimenti Magazzino (File CSV)")
            
            # Carica log se esiste
            log_file = "data/magazzino_log.csv"
            
            if os.path.exists(log_file):
                try:
                    df_log = pd.read_csv(log_file)
                    
                    # Verifica colonne
                    if df_log.empty:
                        st.info("Il log del magazzino è vuoto.")
                    else:
                        # Filtri
                        col_filtro1, col_filtro2 = st.columns(2)
                        
                        with col_filtro1:
                            tipo_movimento = st.multiselect(
                                "Filtra per tipo (magazzino):",
                                df_log['tipo'].unique() if 'tipo' in df_log.columns else [],
                                default=df_log['tipo'].unique() if 'tipo' in df_log.columns else []
                            )
                        
                        with col_filtro2:
                            if 'data' in df_log.columns:
                                # Converti data
                                df_log['data'] = pd.to_datetime(df_log['data'], errors='coerce')
                                df_log = df_log.dropna(subset=['data'])
                                
                                if not df_log.empty:
                                    data_min = df_log['data'].min().date()
                                    data_max = df_log['data'].max().date()
                                    
                                    date_range = st.date_input(
                                        "Intervallo date:",
                                        value=(data_min, data_max),
                                        min_value=data_min,
                                        max_value=data_max
                                    )
                                    
                                    if len(date_range) == 2:
                                        start_date, end_date = date_range
                                        df_log = df_log[
                                            (df_log['data'].dt.date >= start_date) & 
                                            (df_log['data'].dt.date <= end_date)
                                        ]
                        
                        # Applica filtro tipo
                        if tipo_movimento and 'tipo' in df_log.columns:
                            df_log = df_log[df_log['tipo'].isin(tipo_movimento)]
                        
                        # Mostra log
                        st.dataframe(
                            df_log.sort_values('data', ascending=False),
                            use_container_width=True,
                            column_config={
                                "data": st.column_config.DatetimeColumn(
                                    "Data/Ora",
                                    format="DD/MM/YYYY HH:mm"
                                ),
                                "ingrediente": "Ingrediente",
                                "quantita_kg": st.column_config.NumberColumn(
                                    "Quantità (kg)",
                                    format="%.2f"
                                ),
                                "motivo": "Motivo",
                                "tipo": "Tipo",
                                "fornitore": "Fornitore"
                            }
                        )
                        
                        # Statistiche log magazzino
                        st.subheader("📊 Statistiche Movimenti Magazzino")
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        
                        with col_stat1:
                            if 'tipo' in df_log.columns:
                                ingressi = df_log[df_log['tipo'] == 'INGRESSO']['quantita_kg'].sum()
                                st.metric("Totale Ingressi", f"{ingressi:.2f} kg")
                        
                        with col_stat2:
                            if 'tipo' in df_log.columns:
                                uscite = abs(df_log[df_log['tipo'] == 'USCITA']['quantita_kg'].sum())
                                st.metric("Totale Uscite", f"{uscite:.2f} kg")
                        
                        with col_stat3:
                            if 'tipo' in df_log.columns:
                                saldo = ingressi - uscite
                                st.metric("Saldo Netto", f"{saldo:.2f} kg", 
                                         delta_color="normal" if saldo >= 0 else "inverse")
                        
                        # Grafico movimenti nel tempo
                        if 'data' in df_log.columns and not df_log.empty and 'tipo' in df_log.columns:
                            df_log_giorno = df_log.copy()
                            df_log_giorno['data_giorno'] = df_log_giorno['data'].dt.date
                            
                            movimenti_giorno = df_log_giorno.groupby(
                                ['data_giorno', 'tipo']
                            )['quantita_kg'].sum().reset_index()
                            
                            if not movimenti_giorno.empty:
                                fig = px.line(
                                    movimenti_giorno,
                                    x='data_giorno',
                                    y='quantita_kg',
                                    color='tipo',
                                    title='Movimenti Magazzino nel Tempo',
                                    labels={'data_giorno': 'Data', 'quantita_kg': 'Quantità (kg)'},
                                    markers=True
                                )
                                st.plotly_chart(fig, use_container_width=True)
                
                except Exception as e:
                    registra_log("ERRORE", "Errore lettura log magazzino", str(e))
                    st.error(f"Errore nella lettura del log: {str(e)}")
            else:
                st.info("Nessun movimento registrato nel log del magazzino.")
                
                if st.button("📁 Crea file log vuoto"):
                    registra_log("CREAZIONE", "Creazione file log magazzino")
                    # Crea file log con intestazione
                    log_df = pd.DataFrame(columns=['data', 'ingrediente', 'quantita_kg', 
                                                  'tipo', 'motivo', 'fornitore'])
                    log_df.to_csv(log_file, index=False)
                    st.success("File log creato!")
                    st.rerun()
    
    elif pagina == "📋 Pianificazione Produzione":
        # [Mantieni la stessa implementazione della pianificazione produzione]
        st.header("📋 Pianificazione Produzione Ottimizzata")
        registra_log("PAGINA", "Accesso Pianificazione Produzione")
        
        st.info("""
        Pianifica la produzione considerando gli ordini e i vincoli di magazzino.
        Il sistema ottimizzerà automaticamente la produzione in base alla strategia selezionata.
        """)
        
        # Configurazione piano
        col_strat, col_info = st.columns(2)
        
        with col_strat:
            strategia = st.selectbox(
                "Strategia di ottimizzazione:",
                ["profitto", "soddisfazione_ordini"],
                format_func=lambda x: "💰 Massimizza Profitto" if x == "profitto" 
                                    else "✅ Massimizza Soddisfazione Ordini",
                help="Scegli come ottimizzare la produzione"
            )
        
        with col_info:
            st.metric(
                "Prodotti Disponibili",
                len(analyzer.df_combinato),
                help="Numero totale di prodotti che possono essere prodotti"
            )
        
        st.markdown("---")
        st.subheader("📝 Aggiungi Ordini alla Pianificazione")
        
        # Gestione ordini
        col_prod, col_qta, col_btn = st.columns([3, 2, 1])
        
        with col_prod:
            nuovo_prodotto = st.selectbox(
                "Prodotto:",
                analyzer.df_combinato['nome_pane'].tolist(),
                key="ordine_prodotto"
            )
        
        with col_qta:
            nuova_quantita = st.number_input(
                "Quantità (kg):",
                min_value=1.0,
                max_value=10000.0,
                value=100.0,
                step=10.0,
                key="ordine_quantita"
            )
        
        with col_btn:
            st.write("")  # Spazio verticale
            if st.button("➕ Aggiungi", key="aggiungi_ordine"):
                st.session_state.ordini_pianificazione.append({
                    'nome_pane': nuovo_prodotto,
                    'quantita_kg': nuova_quantita,
                    'id': f"ORD_{len(st.session_state.ordini_pianificazione)+1:03d}"
                })
                registra_log("ORDINE", f"Aggiunto ordine: {nuova_quantita}kg di {nuovo_prodotto}")
                st.success(f"Ordine aggiunto: {nuova_quantita} kg di {nuovo_prodotto}")
        
        # Visualizza ordini
        if st.session_state.ordini_pianificazione:
            st.subheader(f"📋 Ordini in Pianificazione ({len(st.session_state.ordini_pianificazione)})")
            
            df_ordini = pd.DataFrame(st.session_state.ordini_pianificazione)
            
            # Calcola totali
            totale_kg = df_ordini['quantita_kg'].sum()
            prodotti_unici = df_ordini['nome_pane'].nunique()
            
            col_tot1, col_tot2, col_tot3 = st.columns(3)
            
            with col_tot1:
                st.metric("Prodotti Unici", prodotti_unici)
            
            with col_tot2:
                st.metric("Quantità Totale", f"{totale_kg:.1f} kg")
            
            with col_tot3:
                st.metric("Ordini Totali", len(st.session_state.ordini_pianificazione))
            
            # Tabella ordini con possibilità di rimozione
            st.write("**Dettaglio Ordini:**")
            
            # Crea lista per editing
            for i, ordine in enumerate(st.session_state.ordini_pianificazione):
                col_ord1, col_ord2, col_ord3, col_ord4 = st.columns([3, 2, 1, 1])
                
                with col_ord1:
                    st.write(f"**{ordine['nome_pane']}**")
                
                with col_ord2:
                    st.write(f"{ordine['quantita_kg']:.1f} kg")
                
                with col_ord3:
                    st.write(ordine.get('id', f"#{i+1}"))
                
                with col_ord4:
                    if st.button("🗑️", key=f"remove_{i}"):
                        registra_log("ORDINE", f"Rimosso ordine: {ordine['quantita_kg']}kg di {ordine['nome_pane']}")
                        st.session_state.ordini_pianificazione.pop(i)
                        st.rerun()
            
            # Pulsanti azione
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if st.button("🎯 Genera Piano di Produzione", type="primary"):
                    registra_log("PIANIFICAZIONE", f"Generazione piano produzione con strategia: {strategia}", f"Ordini: {len(st.session_state.ordini_pianificazione)}")
                    with st.spinner("Ottimizzazione in corso..."):
                        try:
                            piano = analyzer.pianifica_produzione(
                                st.session_state.ordini_pianificazione,
                                strategia
                            )
                            
                            st.session_state.last_report = piano
                            registra_log("SUCCESSO", "Piano produzione generato", f"Ordini soddisfatti: {len(piano.get('ordini_soddisfatti', []))}")
                            
                            # Mostra risultati
                            st.subheader("📋 Piano di Produzione Generato")
                            
                            # Sommario
                            col_ris1, col_ris2, col_ris3, col_ris4 = st.columns(4)
                            
                            with col_ris1:
                                st.metric(
                                    "Ordini Soddisfatti",
                                    len(piano.get('ordini_soddisfatti', [])),
                                    help="Ordini che possono essere prodotti completamente"
                                )
                            
                            with col_ris2:
                                st.metric(
                                    "Ordini Parziali",
                                    len(piano.get('ordini_parziali', [])),
                                    delta_color="off"
                                )
                            
                            with col_ris3:
                                st.metric(
                                    "Ordini Non Soddisfatti",
                                    len(piano.get('ordini_non_soddisfatti', [])),
                                    delta_color="inverse"
                                )
                            
                            with col_ris4:
                                if piano.get('piano_completo', False):
                                    st.success("✅ Piano Completo")
                                else:
                                    st.warning("⚠️ Piano Parziale")
                            
                            # Dettaglio piano in tabs
                            tabs_piano = st.tabs([
                                "✅ Ordini Soddisfatti", 
                                "⚠️ Ordini Parziali", 
                                "❌ Ordini Non Soddisfatti",
                                "📊 Dettaglio Costi"
                            ])
                            
                            with tabs_piano[0]:
                                if piano.get('ordini_soddisfatti'):
                                    df_soddisfatti = pd.DataFrame(piano['ordini_soddisfatti'])
                                    st.dataframe(
                                        df_soddisfatti,
                                        use_container_width=True,
                                        column_config={
                                            "nome_pane": "Prodotto",
                                            "quantita_richiesta_kg": st.column_config.NumberColumn(
                                                "Richiesto (kg)",
                                                format="%.1f kg"
                                            ),
                                            "quantita_prodotta_kg": st.column_config.NumberColumn(
                                                "Prodotto (kg)",
                                                format="%.1f kg"
                                            )
                                        }
                                    )
                                else:
                                    st.info("Nessun ordine soddisfatto completamente.")
                            
                            with tabs_piano[1]:
                                if piano.get('ordini_parziali'):
                                    df_parziali = pd.DataFrame(piano['ordini_parziali'])
                                    st.dataframe(
                                        df_parziali,
                                        use_container_width=True,
                                        column_config={
                                            "nome_pane": "Prodotto",
                                            "quantita_richiesta_kg": st.column_config.NumberColumn(
                                                "Richiesto (kg)",
                                                format="%.1f kg"
                                            ),
                                            "quantita_prodotta_kg": st.column_config.NumberColumn(
                                                "Prodotto (kg)",
                                                format="%.1f kg"
                                            ),
                                            "percentuale_soddisfatta": st.column_config.NumberColumn(
                                                "Soddisfatto (%)",
                                                format="%.1f%%"
                                            )
                                        }
                                    )
                                else:
                                    st.info("Nessun ordine parziale.")
                            
                            with tabs_piano[2]:
                                if piano.get('ordini_non_soddisfatti'):
                                    df_non_soddisfatti = pd.DataFrame(piano['ordini_non_soddisfatti'])
                                    st.dataframe(
                                        df_non_soddisfatti,
                                        use_container_width=True
                                    )
                                else:
                                    st.info("Nessun ordine non soddisfatto.")
                            
                            with tabs_piano[3]:
                                # Mostra costi e tempi
                                col_costi1, col_costi2, col_costi3 = st.columns(3)
                                
                                with col_costi1:
                                    st.metric(
                                        "Costo Totale Stimato",
                                        fmt_euro(piano.get('costo_totale', 0), 2),
                                        help="Costo totale di produzione stimato"
                                    )
                                
                                with col_costi2:
                                    st.metric(
                                        "Tempo Totale Stimato",
                                        f"{piano.get('tempo_totale_ore', 0):.1f} ore",
                                        help="Tempo totale di produzione stimato"
                                    )
                                
                                with col_costi3:
                                    st.metric(
                                        "Giorni Lavorativi",
                                        fmt_numero(piano.get('tempo_totale_giorni', 0), 1),
                                        help="Giorni lavorativi necessari"
                                    )
                                
                                # Utilizzo ingredienti
                                st.subheader("📦 Utilizzo Ingredienti")
                                if piano.get('utilizzo_ingredienti'):
                                    df_utilizzo = pd.DataFrame.from_dict(
                                        piano['utilizzo_ingredienti'], 
                                        orient='index',
                                        columns=['quantita_utilizzata_kg']
                                    ).reset_index()
                                    df_utilizzo.columns = ['Ingrediente', 'Quantità Utilizzata (kg)']
                                    
                                    st.dataframe(
                                        df_utilizzo,
                                        use_container_width=True,
                                        column_config={
                                            "Ingrediente": "Ingrediente",
                                            "Quantità Utilizzata (kg)": st.column_config.NumberColumn(
                                                "Quantità (kg)",
                                                format="%.3f kg"
                                            )
                                        }
                                    )
                            
                            # Azioni sul piano
                            st.markdown("---")
                            st.subheader("⚙️ Azioni")
                            
                            col_act1, col_act2, col_act3 = st.columns(3)
                            
                            with col_act1:
                                if st.button("📥 Salva Piano", help="Salva il piano in formato JSON"):
                                    registra_log("SALVATAGGIO", "Salvataggio piano produzione")
                                    nome_file = f"data/piano_produzione_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                                    try:
                                        with open(nome_file, 'w', encoding='utf-8') as f:
                                            json.dump(piano, f, indent=2, ensure_ascii=False)
                                        registra_log("SUCCESSO", f"Piano salvato: {nome_file}")
                                        st.success(f"Piano salvato come `{nome_file}`")
                                    except Exception as e:
                                        registra_log("ERRORE", "Errore salvataggio piano", str(e))
                                        st.error(f"Errore nel salvataggio: {str(e)}")
                            
                            with col_act2:
                                if st.button("🔄 Applica Piano", type="primary"):
                                    registra_log("APPLICAZIONE", "Applicazione piano produzione al magazzino")
                                    # Calcola utilizzo totale ingredienti
                                    utilizzo_totale = {}
                                    
                                    # Da ordini soddisfatti
                                    for ordine in piano.get('ordini_soddisfatti', []):
                                        nome_pane = ordine['nome_pane']
                                        quantita_kg = ordine.get('quantita_prodotta_kg', 0)
                                        
                                        if quantita_kg > 0:
                                            ingredienti_prodotto = analyzer.df_ingredienti[
                                                analyzer.df_ingredienti['nome_pane'] == nome_pane
                                            ]
                                            
                                            for _, ingrediente in ingredienti_prodotto.iterrows():
                                                nome_ing = ingrediente['ingrediente']
                                                quantita_per_100kg = ingrediente['quantita_kg_per_100kg_prodotto']
                                                quantita_utilizzata = quantita_per_100kg * (quantita_kg / 100)
                                                
                                                if nome_ing not in utilizzo_totale:
                                                    utilizzo_totale[nome_ing] = 0
                                                utilizzo_totale[nome_ing] += quantita_utilizzata
                                    
                                    # Da ordini parziali
                                    for ordine in piano.get('ordini_parziali', []):
                                        nome_pane = ordine['nome_pane']
                                        quantita_kg = ordine.get('quantita_prodotta_kg', 0)
                                        
                                        if quantita_kg > 0:
                                            ingredienti_prodotto = analyzer.df_ingredienti[
                                                analyzer.df_ingredienti['nome_pane'] == nome_pane
                                            ]
                                            
                                            for _, ingrediente in ingredienti_prodotto.iterrows():
                                                nome_ing = ingrediente['ingrediente']
                                                quantita_per_100kg = ingrediente['quantita_kg_per_100kg_prodotto']
                                                quantita_utilizzata = quantita_per_100kg * (quantita_kg / 100)
                                                
                                                if nome_ing not in utilizzo_totale:
                                                    utilizzo_totale[nome_ing] = 0
                                                utilizzo_totale[nome_ing] += quantita_utilizzata
                                    
                                    # Aggiorna magazzino
                                    if utilizzo_totale:
                                        if analyzer.aggiorna_magazzino(utilizzo_totale, "Piano produzione ottimizzato"):
                                            registra_log("SUCCESSO", "Magazzino aggiornato dal piano produzione")
                                            st.success("✅ Magazzino aggiornato con successo!")
                                            st.session_state.ordini_pianificazione = []
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            registra_log("ERRORE", "Errore aggiornamento magazzino da piano")
                                            st.error("❌ Errore nell'aggiornamento del magazzino")
                                    else:
                                        registra_log("ATTENZIONE", "Nessuna produzione da applicare nel piano")
                                        st.warning("Nessuna produzione da applicare")
                            
                            with col_act3:
                                if st.button("🖨️ Stampa Riepilogo"):
                                    registra_log("STAMPA", "Richiesta stampa riepilogo piano")
                                    st.info("Funzionalità di stampa da implementare")
                        
                        except Exception as e:
                            registra_log("ERRORE", "Errore generazione piano produzione", str(e))
                            st.error(f"Errore nella generazione del piano: {str(e)}")
            
            with col_act2:
                if st.button("🗑️ Pulisci Tutti gli Ordini"):
                    registra_log("PULIZIA", "Pulizia di tutti gli ordini di pianificazione")
                    st.session_state.ordini_pianificazione = []
                    st.rerun()
            
            with col_act3:
                if st.button("💾 Salva Ordini"):
                    if st.session_state.ordini_pianificazione:
                        registra_log("SALVATAGGIO", "Salvataggio ordini di pianificazione")
                        df_salva = pd.DataFrame(st.session_state.ordini_pianificazione)
                        nome_file = f"data/ordini_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        df_salva.to_csv(nome_file, index=False)
                        registra_log("SUCCESSO", f"Ordini salvati in {nome_file}")
                        st.success(f"Ordini salvati in {nome_file}")
        
        else:
            st.info("👆 Aggiungi ordini per generare un piano di produzione.")
            
            # Esempio di ordini rapidi
            st.subheader("💡 Esempi Rapidi")
            
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            
            with col_ex1:
                if st.button("🍞 100kg Pane Comune"):
                    st.session_state.ordini_pianificazione.append({
                        'nome_pane': 'Pane Comune',
                        'quantita_kg': 100,
                        'id': f"ORD_{len(st.session_state.ordini_pianificazione)+1:03d}"
                    })
                    registra_log("ESEMPIO", "Aggiunto ordine esempio: 100kg Pane Comune")
                    st.success("Ordine aggiunto!")
                    st.rerun()
            
            with col_ex2:
                if st.button("🥖 50kg Pane Integrale"):
                    st.session_state.ordini_pianificazione.append({
                        'nome_pane': 'Pane Integrale',
                        'quantita_kg': 50,
                        'id': f"ORD_{len(st.session_state.ordini_pianificazione)+1:03d}"
                    })
                    registra_log("ESEMPIO", "Aggiunto ordine esempio: 50kg Pane Integrale")
                    st.success("Ordine aggiunto!")
                    st.rerun()
            
            with col_ex3:
                if st.button("🥐 80kg Focaccia"):
                    st.session_state.ordini_pianificazione.append({
                        'nome_pane': 'Focaccia',
                        'quantita_kg': 80,
                        'id': f"ORD_{len(st.session_state.ordini_pianificazione)+1:03d}"
                    })
                    registra_log("ESEMPIO", "Aggiunto ordine esempio: 80kg Focaccia")
                    st.success("Ordine aggiunto!")
                    st.rerun()
    
    elif pagina == "📈 Report & Analytics":
        # [Mantieni la stessa implementazione dei report]
        st.header("📈 Report & Analytics")
        registra_log("PAGINA", "Accesso Report & Analytics")
        
        tab_report, tab_suggerimenti, tab_export = st.tabs([
            "📊 Report Completo", 
            "💡 Suggerimenti", 
            "📤 Esporta Dati"
        ])
        
        with tab_report:
            st.subheader("Report Completo Analisi")
            
            # Statistiche sempre visibili
            st.markdown("---")
            st.subheader("📊 Statistiche Principali")
            
            # Metriche rapide
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric(
                    "🍞 Prodotti",
                    fmt_numero(len(analyzer.df_combinato)),
                    help="Numero totale di prodotti"
                )
            
            with col_m2:
                costo_medio = analyzer.df_combinato['costo_totale_per_100kg'].mean()
                st.metric(
                    "💰 Costo Medio",
                    fmt_euro(costo_medio, 2),
                    help="Costo medio per 100kg"
                )
            
            with col_m3:
                st.metric(
                    "📦 Ingredienti",
                    fmt_numero(len(analyzer.df_magazzino)),
                    help="Numero ingredienti magazzino"
                )
            
            with col_m4:
                costo_max = analyzer.df_combinato['costo_totale_per_100kg'].max()
                costo_min = analyzer.df_combinato['costo_totale_per_100kg'].min()
                st.metric(
                    "📈 Range Costi",
                    f"{fmt_euro(costo_max, 0)} - {fmt_euro(costo_min, 0)}",
                    help="Costo massimo e minimo"
                )
            
            st.markdown("---")
            
            # Grafico correlazione ingredienti-produzione
            try:
                # Crea una matrice di correlazione per heatmap più comprensibile
                df_corr = analyzer.df_combinato[
                    ['costo_ingredienti_per_100kg', 'costo_produzione_per_100kg', 'costo_totale_per_100kg']
                ].corr()
                
                fig = go.Figure(data=go.Heatmap(
                    z=df_corr.values,
                    x=['Ingredienti', 'Produzione', 'Totale'],
                    y=['Ingredienti', 'Produzione', 'Totale'],
                    colorscale='RdBu',
                    zmid=0,
                    text=df_corr.values.round(2),
                    texttemplate='%{text}',
                    textfont={"size": 12},
                    colorbar=dict(title="Correlazione"),
                    hovertemplate='%{y} vs %{x}<br>Correlazione: %{z:.3f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title='🔗 Matrice di Correlazione Costi',
                    height=400,
                    font=dict(size=12)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Grafico a linee per trend costi
                fig2_data = analyzer.df_combinato.sort_values('costo_totale_per_100kg').reset_index(drop=True)
                fig2_data['Progressione'] = range(len(fig2_data))
                
                fig2 = go.Figure()
                
                fig2.add_trace(go.Scatter(
                    x=fig2_data['Progressione'],
                    y=fig2_data['costo_ingredienti_per_100kg'],
                    mode='lines',
                    name='Ingredienti',
                    line=dict(color='#3498DB', width=2),
                    hovertemplate='Prodotto %{x}: €%{y:.2f}<extra></extra>'
                ))
                
                fig2.add_trace(go.Scatter(
                    x=fig2_data['Progressione'],
                    y=fig2_data['costo_produzione_per_100kg'],
                    mode='lines',
                    name='Produzione',
                    line=dict(color='#E74C3C', width=2),
                    hovertemplate='Prodotto %{x}: €%{y:.2f}<extra></extra>'
                ))
                
                fig2.update_layout(
                    title='📈 Trend Costi per Componente',
                    xaxis_title='Progressione Prodotti',
                    yaxis_title='Costo (€/100kg)',
                    height=400,
                    hovermode='x unified',
                    plot_bgcolor='rgba(240,240,240,0.3)'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Distribuzione percentuale costi
                fig_dist = analyzer.df_combinato.copy()
                fig_dist['Percentuale Ingredienti'] = (fig_dist['costo_ingredienti_per_100kg'] / 
                                                       fig_dist['costo_totale_per_100kg'] * 100).round(1)
                fig_dist['Percentuale Produzione'] = (fig_dist['costo_produzione_per_100kg'] / 
                                                      fig_dist['costo_totale_per_100kg'] * 100).round(1)
                
                fig3 = px.histogram(
                    fig_dist,
                    x='Percentuale Ingredienti',
                    nbins=15,
                    title='📊 Distribuzione: % Ingredienti vs Costo Totale',
                    labels={'Percentuale Ingredienti': 'Percentuale Ingredienti sul Costo'},
                    color_discrete_sequence=['#2ECC71'],
                    opacity=0.85
                )
                
                fig3.update_layout(
                    height=400,
                    showlegend=False,
                    plot_bgcolor='rgba(240,240,240,0.3)',
                    xaxis_title='% Ingredienti sul Costo Totale',
                    yaxis_title='Numero di Prodotti'
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                registra_log("GRAFICI", "Grafico correlazione costi generato")
            except Exception as e:
                registra_log("ERRORE", "Grafico correlazione", str(e))
                st.warning(f"Grafico correlazione non disponibile: {str(e)}")
            
            # Distribuzione costi
            try:
                # Calcola statistiche
                media = analyzer.df_combinato['costo_totale_per_100kg'].mean()
                mediana = analyzer.df_combinato['costo_totale_per_100kg'].median()
                
                fig2 = px.histogram(
                    analyzer.df_combinato,
                    x='costo_totale_per_100kg',
                    nbins=20,
                    title='📊 Distribuzione Costi Totali per Prodotto',
                    labels={'costo_totale_per_100kg': 'Costo per 100kg (€)', 'count': 'Numero Prodotti'},
                    color_discrete_sequence=['#3498DB'],
                    opacity=0.8
                )
                
                # Aggiungi linee per media e mediana
                fig2.add_vline(
                    x=media,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Media: {fmt_euro(media, 2)}",
                    annotation_position="top left",
                    annotation_font_size=11
                )
                
                fig2.add_vline(
                    x=mediana,
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"Mediana: {fmt_euro(mediana, 2)}",
                    annotation_position="top right",
                    annotation_font_size=11
                )
                
                fig2.update_layout(
                    height=450,
                    showlegend=False,
                    xaxis_title="Costo per 100kg (€)",
                    yaxis_title="Numero di Prodotti",
                    plot_bgcolor='rgba(240,240,240,0.5)',
                    hovermode='x unified',
                    bargap=0.1,
                    font=dict(size=11)
                )
                
                fig2.update_traces(
                    hovertemplate='Range: €%{x:.0f}<br>Prodotti: %{y}<extra></extra>'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                registra_log("GRAFICI", "Grafico distribuzione costi generato")
            except Exception as e:
                registra_log("ERRORE", "Grafico distribuzione", str(e))
                st.warning(f"Grafico distribuzione non disponibile: {str(e)}")
            
            # Top prodotti per rapporto costo/produzione
            st.subheader("📊 Performance Prodotti")
            
            try:
                # Calcola rapporto costo/valore (simulato)
                df_performance = analyzer.df_combinato.copy()
                df_performance['rapporto_costo'] = df_performance['costo_totale_per_100kg'] / df_performance['costo_totale_per_100kg'].mean()
                df_performance['costo_per_kg'] = df_performance['costo_totale_per_100kg'] / 100
                
                # Crea categorizzazione
                df_performance['categoria'] = pd.cut(
                    df_performance['rapporto_costo'],
                    bins=[0, 0.8, 1.2, 2],
                    labels=['💰 Economico', '💵 Standard', '💎 Premium']
                )
                
                # Grafico a barre orizzontali per categoria
                categoria_counts = df_performance['categoria'].value_counts()
                
                fig3 = px.bar(
                    x=categoria_counts.values,
                    y=categoria_counts.index,
                    orientation='h',
                    title='🎯 Distribuzione Prodotti per Categoria di Costo',
                    labels={'x': 'Numero Prodotti', 'y': 'Categoria'},
                    color=categoria_counts.index,
                    color_discrete_map={
                        '💰 Economico': '#2ECC71',
                        '💵 Standard': '#F39C12',
                        '💎 Premium': '#E74C3C'
                    },
                    text=categoria_counts.values
                )
                
                fig3.update_traces(
                    texttemplate='%{x}',
                    textposition='outside',
                    hovertemplate='%{y}<br>Prodotti: %{x}<extra></extra>'
                )
                
                fig3.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title="Numero di Prodotti",
                    yaxis_title="",
                    plot_bgcolor='rgba(240,240,240,0.3)',
                    hovermode='y unified',
                    font=dict(size=11)
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                
                # Grafico box plot per componenti di costo per categoria
                fig4_data = []
                for categoria in ['💰 Economico', '💵 Standard', '💎 Premium']:
                    costi = df_performance[df_performance['categoria'] == categoria]['costo_per_kg'].tolist()
                    fig4_data.append(
                        go.Box(
                            y=costi,
                            name=categoria,
                            marker_color={'💰 Economico': '#2ECC71', '💵 Standard': '#F39C12', '💎 Premium': '#E74C3C'}[categoria]
                        )
                    )
                
                fig4 = go.Figure(data=fig4_data)
                
                fig4.update_layout(
                    title='📦 Distribuzione Costi/kg per Categoria',
                    yaxis_title='Costo per kg (€)',
                    height=350,
                    plot_bgcolor='rgba(240,240,240,0.3)',
                    showlegend=False,
                    font=dict(size=11),
                    hovermode='closest'
                )
                
                st.plotly_chart(fig4, use_container_width=True)
                
                # Aggiunta: statistiche per categoria
                st.markdown("---")
                col_cat1, col_cat2, col_cat3 = st.columns(3)
                
                economici = len(df_performance[df_performance['categoria'] == '💰 Economico'])
                standard = len(df_performance[df_performance['categoria'] == '💵 Standard'])
                premium = len(df_performance[df_performance['categoria'] == '💎 Premium'])
                
                with col_cat1:
                    st.metric("💰 Economici", fmt_numero(economici), help="Prodotti sotto media")
                
                with col_cat2:
                    st.metric("💵 Standard", fmt_numero(standard), help="Prodotti a media")
                
                with col_cat3:
                    st.metric("💎 Premium", fmt_numero(premium), help="Prodotti sopra media")
                
                registra_log("GRAFICI", "Grafico performance prodotti generato")
            except Exception as e:
                registra_log("ERRORE", "Grafico performance", str(e))
                st.warning(f"Analisi performance non disponibile: {str(e)}")
        
        with tab_suggerimenti:
            st.subheader("💡 Suggerimenti Ottimizzazione")
            
            if st.button("🔍 Analizza per Suggerimenti", type="primary"):
                registra_log("ANALISI", "Avvio analisi suggerimenti ottimizzazione")
                with st.spinner("Analizzando dati per suggerimenti..."):
                    try:
                        # Analisi semplice
                        suggerimenti = {
                            'riduzione_costi': [],
                            'ottimizzazione_magazzino': [],
                            'suggerimenti_produzione': []
                        }
                        
                        # Analizza prodotti costosi (top 5)
                        prodotti_costosi = analyzer.df_combinato.nlargest(5, 'costo_totale_per_100kg')
                        for _, prodotto in prodotti_costosi.iterrows():
                            suggerimenti['riduzione_costi'].append({
                                'prodotto': prodotto['nome_pane'],
                                'costo': prodotto['costo_totale_per_100kg'],
                                'costo_ing': prodotto['costo_ingredienti_per_100kg'],
                                'costo_prod': prodotto['costo_produzione_per_100kg']
                            })
                        
                        # Analizza magazzino
                        scorte_basse = analyzer.df_magazzino[
                            analyzer.df_magazzino['quantita_kg'] < analyzer.df_magazzino['scorta_minima']
                        ]
                        for _, ingrediente in scorte_basse.iterrows():
                            suggerimenti['ottimizzazione_magazzino'].append({
                                'ingrediente': ingrediente['ingrediente'],
                                'quantita_attuale': ingrediente['quantita_kg'],
                                'scorta_minima': ingrediente['scorta_minima'],
                                'deficit': ingrediente['scorta_minima'] - ingrediente['quantita_kg']
                            })
                        
                        registra_log("SUCCESSO", "Analisi suggerimenti completata")
                        
                        # ========== GRAFICO 1: Prodotti più Costosi ==========
                        if suggerimenti.get('riduzione_costi'):
                            st.subheader("💰 Riduzione Costi - Top 5 Prodotti")
                            
                            df_costi_sugg = pd.DataFrame(suggerimenti['riduzione_costi'])
                            
                            # Grafico a barre con breakdown ingredienti/produzione
                            fig_costi = go.Figure(data=[
                                go.Bar(
                                    x=df_costi_sugg['prodotto'],
                                    y=df_costi_sugg['costo_ing'],
                                    name='Costo Ingredienti',
                                    marker_color='#FF6B6B',
                                    hovertemplate='<b>%{x}</b><br>Ingredienti: €%{y:.2f}<extra></extra>'
                                ),
                                go.Bar(
                                    x=df_costi_sugg['prodotto'],
                                    y=df_costi_sugg['costo_prod'],
                                    name='Costo Produzione',
                                    marker_color='#4ECDC4',
                                    hovertemplate='<b>%{x}</b><br>Produzione: €%{y:.2f}<extra></extra>'
                                )
                            ])
                            
                            fig_costi.update_layout(
                                title='📊 Breakdown Costi - I 5 Prodotti più Costosi',
                                xaxis_title='Prodotto',
                                yaxis_title='Costo (€/100kg)',
                                barmode='stack',
                                height=400,
                                plot_bgcolor='rgba(240,240,240,0.3)',
                                hovermode='x unified',
                                font=dict(size=11)
                            )
                            
                            st.plotly_chart(fig_costi, use_container_width=True)
                            
                            # Tabella con consigli
                            st.write("**Azioni Suggerite:**")
                            for idx, sugg in enumerate(df_costi_sugg.iterrows(), 1):
                                sugg_data = sugg[1]
                                col_c1, col_c2, col_c3 = st.columns([1, 3, 2])
                                with col_c1:
                                    st.error(f"#{idx}")
                                with col_c2:
                                    st.write(f"**{sugg_data['prodotto']}** - €{sugg_data['costo']:.2f}/100kg")
                                with col_c3:
                                    # Suggerimento basato sul breakdown
                                    if sugg_data['costo_ing'] > sugg_data['costo_prod']:
                                        st.info("🔍 Ottimizzare ingredienti")
                                    else:
                                        st.info("⚙️ Ottimizzare produzione")
                        
                        # ========== GRAFICO 2: Magazzino in Deficit ==========
                        if suggerimenti.get('ottimizzazione_magazzino'):
                            st.markdown("---")
                            st.subheader("📦 Ottimizzazione Magazzino - Scorte Critiche")
                            
                            df_mag_sugg = pd.DataFrame(suggerimenti['ottimizzazione_magazzino'])
                            
                            # Grafico gauge per ogni ingrediente
                            col_mag_left, col_mag_right = st.columns(2)
                            
                            with col_mag_left:
                                # Grafico a barre orizzontali - Deficit
                                fig_deficit = px.bar(
                                    df_mag_sugg,
                                    y='ingrediente',
                                    x='deficit',
                                    orientation='h',
                                    title='⚠️ Deficit Magazzino (kg necessari)',
                                    labels={'deficit': 'kg da Rifornire', 'ingrediente': 'Ingrediente'},
                                    color='deficit',
                                    color_continuous_scale='Reds',
                                    text='deficit'
                                )
                                
                                fig_deficit.update_traces(
                                    texttemplate='%{x:.1f} kg',
                                    textposition='auto',
                                    hovertemplate='<b>%{y}</b><br>Deficit: %{x:.1f} kg<extra></extra>'
                                )
                                
                                fig_deficit.update_layout(
                                    height=350,
                                    showlegend=False,
                                    xaxis_title='kg da Rifornire',
                                    yaxis_title='',
                                    plot_bgcolor='rgba(240,240,240,0.3)',
                                    margin=dict(l=150)
                                )
                                
                                st.plotly_chart(fig_deficit, use_container_width=True)
                            
                            with col_mag_right:
                                # Gauge showing percentage
                                fig_gauge = go.Figure()
                                
                                for idx, (_, row) in enumerate(df_mag_sugg.iterrows()):
                                    percentuale = (row['quantita_attuale'] / row['scorta_minima']) * 100
                                    
                                    fig_gauge.add_trace(go.Indicator(
                                        mode="gauge+number+delta",
                                        value=percentuale,
                                        domain={'x': [0, 1], 'y': [0, 0.5]},
                                        title={'text': row['ingrediente']},
                                        delta={'reference': 100, 'suffix': "% minimo"},
                                        gauge={
                                            'axis': {'range': [0, 200]},
                                            'bar': {'color': '#E74C3C' if percentuale < 100 else '#F39C12'},
                                            'steps': [
                                                {'range': [0, 50], 'color': 'rgba(231, 76, 60, 0.1)'},
                                                {'range': [50, 100], 'color': 'rgba(243, 156, 18, 0.1)'},
                                                {'range': [100, 150], 'color': 'rgba(46, 204, 113, 0.1)'},
                                                {'range': [150, 200], 'color': 'rgba(46, 204, 113, 0.2)'}
                                            ],
                                            'threshold': {
                                                'line': {'color': "red", 'width': 4},
                                                'thickness': 0.75,
                                                'value': 100
                                            }
                                        }
                                    ))
                                
                                fig_gauge.update_layout(
                                    title_text="📊 Livelli Scorta (%)",
                                    height=350 * min(len(df_mag_sugg), 3),
                                    font=dict(size=10)
                                )
                                
                                st.plotly_chart(fig_gauge, use_container_width=True)
                        
                        if not (suggerimenti.get('riduzione_costi') or 
                               suggerimenti.get('ottimizzazione_magazzino')):
                            st.info("✅ Sistema ben ottimizzato! Nessun suggerimento critico.")
                            registra_log("OTTIMIZZAZIONE", "Sistema ottimizzato, nessun suggerimento critico")
                            
                    except Exception as e:
                        registra_log("ERRORE", "Errore analisi suggerimenti", str(e))
                        st.error(f"Errore nell'analisi: {str(e)}")
           
            # Analisi automatica semplice
            st.markdown("---")
            st.subheader("📊 Analisi Automatica")
           
            if st.button("🔄 Esegui Analisi Rapida"):
                registra_log("ANALISI", "Avvio analisi rapida")
                with st.spinner("Analizzando..."):
                    try:
                        # Analisi prodotti
                        costo_max = analyzer.df_combinato['costo_totale_per_100kg'].max()
                        costo_min = analyzer.df_combinato['costo_totale_per_100kg'].min()
                        costo_medio = analyzer.df_combinato['costo_totale_per_100kg'].mean()
                       
                        col_ana1, col_ana2, col_ana3 = st.columns(3)
                       
                        with col_ana1:
                            prodotto_costoso = analyzer.df_combinato.loc[
                                analyzer.df_combinato['costo_totale_per_100kg'].idxmax()
                            ]['nome_pane']
                            st.metric("Prodotto più Costoso", prodotto_costoso,
                                     fmt_euro(costo_max, 2))
                       
                        with col_ana2:
                            prodotto_economico = analyzer.df_combinato.loc[
                                analyzer.df_combinato['costo_totale_per_100kg'].idxmin()
                            ]['nome_pane']
                            st.metric("Prodotto più Economico", prodotto_economico,
                                     fmt_euro(costo_min, 2))
                       
                        with col_ana3:
                            st.metric("Differenza Costi", fmt_euro(costo_max - costo_min, 2),
                                     f"{((costo_max - costo_min)/costo_medio*100):.0f}% dalla media")
                       
                        # Analisi magazzino
                        st.subheader("📦 Analisi Scorte")
                       
                        ingredienti_critici = analyzer.df_magazzino[
                            analyzer.df_magazzino['quantita_kg'] <
                            analyzer.df_magazzino['scorta_minima'] * 0.5
                        ]
                       
                        if not ingredienti_critici.empty:
                            st.warning(f"⚠️ {len(ingredienti_critici)} ingredienti CRITICI:")
                            for _, ing in ingredienti_critici.iterrows():
                                st.write(f"• {ing['ingrediente']}: {ing['quantita_kg']:.1f} kg "
                                        f"(min: {ing['scorta_minima']:.1f} kg)")
                        else:
                            st.success("✅ Nessun ingrediente in situazione critica")
                       
                        registra_log("SUCCESSO", "Analisi rapida completata")
                           
                    except Exception as e:
                        registra_log("ERRORE", "Errore analisi rapida", str(e))
                        st.error(f"Errore nell'analisi rapida: {str(e)}")
       
        with tab_export:
            st.subheader("📤 Esporta Dati")
            registra_log("ESPORTAZIONE", "Accesso modulo esportazione")
           
            st.info("Esporta i dati in vari formati per analisi esterne.")
           
            # Formato di esportazione
            formato = st.radio(
                "Formato di esportazione:",
                ["CSV", "Excel", "JSON"],
                horizontal=True
            )
           
            # Dati da esportare
            dati_export = st.multiselect(
                "Seleziona dati da esportare:",
                ["Prodotti e Costi", "Magazzino", "Ingredienti per Prodotto", "Log Movimenti"],
                default=["Prodotti e Costi", "Magazzino"]
            )
           
            if st.button("📤 Genera File di Esportazione", type="primary"):
                registra_log("ESPORTAZIONE", f"Generazione esportazione in formato {formato}", f"Dati: {', '.join(dati_export)}")
                with st.spinner("Preparando esportazione..."):
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        files_created = []
                       
                        # Esporta Prodotti e Costi
                        if "Prodotti e Costi" in dati_export:
                            df_prodotti = analyzer.df_combinato.copy()
                            filename = f"esportazione_prodotti_{timestamp}"
                           
                            if formato == "CSV":
                                df_prodotti.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
                                files_created.append(f"{filename}.csv")
                            elif formato == "Excel":
                                df_prodotti.to_excel(f"{filename}.xlsx", index=False)
                                files_created.append(f"{filename}.xlsx")
                            else:  # JSON
                                df_prodotti.to_json(f"{filename}.json", orient='records', indent=2)
                                files_created.append(f"{filename}.json")
                       
                        # Esporta Magazzino
                        if "Magazzino" in dati_export:
                            df_magazzino_exp = analyzer.df_magazzino.copy()
                            filename = f"esportazione_magazzino_{timestamp}"
                           
                            if formato == "CSV":
                                df_magazzino_exp.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
                                files_created.append(f"{filename}.csv")
                            elif formato == "Excel":
                                df_magazzino_exp.to_excel(f"{filename}.xlsx", index=False)
                                files_created.append(f"{filename}.xlsx")
                            else:  # JSON
                                df_magazzino_exp.to_json(f"{filename}.json", orient='records', indent=2)
                                files_created.append(f"{filename}.json")
                       
                        # Esporta Ingredienti per Prodotto
                        if "Ingredienti per Prodotto" in dati_export and hasattr(analyzer, 'df_ingredienti'):
                            df_ingredienti_exp = analyzer.df_ingredienti.copy()
                            filename = f"esportazione_ingredienti_{timestamp}"
                           
                            if formato == "CSV":
                                df_ingredienti_exp.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
                                files_created.append(f"{filename}.csv")
                            elif formato == "Excel":
                                df_ingredienti_exp.to_excel(f"{filename}.xlsx", index=False)
                                files_created.append(f"{filename}.xlsx")
                            else:  # JSON
                                df_ingredienti_exp.to_json(f"{filename}.json", orient='records', indent=2)
                                files_created.append(f"{filename}.json")
                       
                        # Esporta Log Movimenti
                        if "Log Movimenti" in dati_export and os.path.exists("data/magazzino_log.csv"):
                            df_log_exp = pd.read_csv("data/magazzino_log.csv")
                            filename = f"esportazione_log_{timestamp}"
                           
                            if formato == "CSV":
                                df_log_exp.to_csv(f"{filename}.csv", index=False, encoding='utf-8')
                                files_created.append(f"{filename}.csv")
                            elif formato == "Excel":
                                df_log_exp.to_excel(f"{filename}.xlsx", index=False)
                                files_created.append(f"{filename}.xlsx")
                            else:  # JSON
                                df_log_exp.to_json(f"{filename}.json", orient='records', indent=2)
                                files_created.append(f"{filename}.json")
                       
                        if files_created:
                            registra_log("SUCCESSO", f"File esportazione creati: {len(files_created)}")
                            st.success(f"✅ File creati: {', '.join(files_created)}")
                           
                            # Pulsante per scaricare ZIP (solo visualizzazione)
                            if len(files_created) > 1:
                                st.info("📁 I file sono stati salvati nella directory corrente.")
                        else:
                            registra_log("ATTENZIONE", "Nessun file creato nell'esportazione")
                            st.warning("Nessun file creato. Verifica le selezioni.")
                           
                    except Exception as e:
                        registra_log("ERRORE", "Errore esportazione dati", str(e))
                        st.error(f"Errore nell'esportazione: {str(e)}")
           
            # Download diretto dati principali
            st.markdown("---")
            st.subheader("📥 Download Diretto")
           
            # Crea dataframe per download
            try:
                df_download = analyzer.df_combinato[[
                    'nome_pane', 'costo_ingredienti_per_100kg',
                    'costo_produzione_per_100kg', 'costo_totale_per_100kg'
                ]].copy()
               
                # Aggiungi costo per kg
                df_download['costo_per_kg'] = df_download['costo_totale_per_100kg'] / 100
               
                csv = df_download.to_csv(index=False, encoding='utf-8')
               
                st.download_button(
                    label="📊 Scarica Dati Prodotti (CSV)",
                    data=csv,
                    file_name=f"dati_prodotti_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    help="Scarica i dati principali dei prodotti in formato CSV"
                )
            except Exception as e:
                registra_log("ERRORE", "Errore preparazione download", str(e))
                st.error(f"Errore nella preparazione del download: {str(e)}")
   
    elif pagina == "🔮 Previsioni Mercato":
        # Chiama la nuova funzione show_forecast_page()
        show_forecast_page()
   
    elif pagina == "⚙️ Configurazione":
        st.header("⚙️ Configurazione Sistema")
        registra_log("PAGINA", "Accesso Configurazione Sistema")
        
        tab_config, tab_info, tab_backup = st.tabs(["Impostazioni", "Informazioni Sistema", "Backup & Ripristino"])
        
        with tab_config:
            st.subheader("Impostazioni Applicazione")
   
            # Inizializza session state per impostazioni se non esiste
            if 'impostazioni' not in st.session_state:
                st.session_state.impostazioni = {
                    'lingua': 'Italiano',
                    'fuso_orario': 'Europe/Rome',
                    'notifiche': True
                }

            # Impostazioni generali
            with st.expander("⚙️ Impostazioni Generali", expanded=True):
                col_gen1, col_gen2 = st.columns(2)

                with col_gen1:
                    # Crea un nuovo selectbox per la lingua con valore corrente
                    nuova_lingua = st.selectbox(
                        "Lingua interfaccia:",
                        ["Italiano", "English", "Español"],
                        index=["Italiano", "English", "Español"].index(st.session_state.impostazioni['lingua'])
                    )

                with col_gen2:
                    # Crea un nuovo selectbox per il fuso orario con valore corrente
                    nuovo_fuso = st.selectbox(
                        "Fuso orario:",
                        ["Europe/Rome", "UTC", "America/New_York"],
                        index=["Europe/Rome", "UTC", "America/New_York"].index(st.session_state.impostazioni['fuso_orario'])
                    )
       
                nuove_notifiche = st.checkbox("Attiva notifiche", value=st.session_state.impostazioni['notifiche'])
       
                col_save, col_reset = st.columns(2)
       
                with col_save:
                    if st.button("💾 Salva Impostazioni", type="primary", key="save_settings_general"):
                        # Aggiorna le impostazioni
                        impostazioni_precedenti = st.session_state.impostazioni.copy()
                        st.session_state.impostazioni = {
                            'lingua': nuova_lingua,
                            'fuso_orario': nuovo_fuso,
                            'notifiche': nuove_notifiche
                        }
               
                        # Verifica se la lingua è stata cambiata
                        lingua_cambiata = impostazioni_precedenti['lingua'] != nuova_lingua

                        registra_log("CONFIGURAZIONE", "Impostazioni generali salvate",
                                f"Lingua: {nuova_lingua}, Fuso: {nuovo_fuso}, Notifiche: {nuove_notifiche}")
               
                        # Mostra messaggio in base alla lingua selezionata
                        if lingua_cambiata:
                            if nuova_lingua == "English":
                                st.success("✅ Settings saved successfully!")
                                st.info("⚠️ To fully apply language changes, please restart the application.")
                            elif nuova_lingua == "Español":
                                st.success("✅ ¡Configuración guardada correctamente!")
                                st.info("⚠️ Para aplicar completamente los cambios de idioma, reinicie la aplicación.")
                            else:
                                st.success("✅ Impostazioni salvate con successo!")
                                st.info("⚠️ Per applicare completamente i cambiamenti di lingua, riavvia l'applicazione.")
                        else:
                            if nuova_lingua == "English":
                                st.success("✅ Settings saved successfully!")
                            elif nuova_lingua == "Español":
                                st.success("✅ ¡Configuración guardada correctamente!")
                            else:
                                st.success("✅ Impostazioni salvate con successo!")
       
                with col_reset:
                    if st.button("🔄 Ripristina Default", key="reset_default_general"):
                        st.session_state.impostazioni = {
                            'lingua': 'Italiano',
                            'fuso_orario': 'Europe/Rome',
                            'notifiche': True
                        }
                        registra_log("CONFIGURAZIONE", "Impostazioni ripristinate ai valori default")
                        st.success("Impostazioni ripristinate ai valori di default!")
                        st.rerun()

            # Mostra le impostazioni correnti
            st.markdown("---")
            st.subheader("Impostazioni Correnti")

            col_curr1, col_curr2, col_curr3 = st.columns(3)
   
            with col_curr1:
                st.metric(
                    "Lingua Attuale",
                    st.session_state.impostazioni['lingua'],
                    help="La lingua corrente dell'interfaccia"
                )
   
            with col_curr2:
                st.metric(
                    "Fuso Orario",
                    st.session_state.impostazioni['fuso_orario'],
                    help="Il fuso orario configurato"
                )

            with col_curr3:
                stato_notifiche = "✅ Attive" if st.session_state.impostazioni['notifiche'] else "❌ Disattive"
                st.metric(
                    "Notifiche",
                    stato_notifiche,
                    help="Stato delle notifiche del sistema"
                )

            # Gestione scorte minime
            st.markdown("---")
            with st.expander("📊 Imposta Scorte Minime", expanded=False):
                st.write("Modifica le scorte minime per ogni ingrediente:")

                df_scorte = analyzer.df_magazzino.copy()

                edited_df = st.data_editor(
                    df_scorte[['ingrediente', 'scorta_minima']],
                    use_container_width=True,
                    column_config={
                        "ingrediente": "Ingrediente",
                        "scorta_minima": st.column_config.NumberColumn(
                            "Scorta Minima (kg)",
                            min_value=0,
                            step=1.0,
                            help="Livello minimo di sicurezza per questo ingrediente"
                        )
                    }
                )

                col_save1, col_save2 = st.columns(2)
       
                with col_save1:
                    if st.button("💾 Salva Scorte Minime", type="primary", key="save_min_stock"):
                        registra_log("CONFIGURAZIONE", "Salvataggio scorte minime")
                        # Aggiorna df_magazzino
                        for idx, row in edited_df.iterrows():
                            analyzer.df_magazzino.loc[
                                analyzer.df_magazzino['ingrediente'] == row['ingrediente'],
                                'scorta_minima'
                            ] = row['scorta_minima']

                        analyzer._salva_magazzino()
                        registra_log("SUCCESSO", "Scorte minime aggiornate")
                        st.success("Scorte minime aggiornate!")

                with col_save2:
                    if st.button("🔄 Ripristina Default", key="reset_stock_default"):
                        registra_log("CONFIGURAZIONE", "Ripristino default scorte minime")
                        st.info("Funzionalità in sviluppo")

            # Reset magazzino
            st.markdown("---")
            with st.expander("🔧 Reset Magazzino", expanded=False):
                st.warning("⚠️ **ATTENZIONE:** Questa operazione resetta il magazzino ai valori iniziali.")
                st.info("Tutti i movimenti verranno mantenuti nel log, ma le quantità attuali saranno ripristinate.")

                col_res1, col_res2 = st.columns(2)

                with col_res1:
                    if st.button("🔄 Reset Magazzino", type="secondary", key="reset_warehouse"):
                        registra_log("RESET", "Reset magazzino ai valori iniziali")
                        # Rimuovi file magazzino
                        magazzino_file = "data/magazzino.csv"
                        if os.path.exists(magazzino_file):
                            os.remove(magazzino_file)

                        # Ricrea analyzer
                        analyzer._init_magazzino()
                        registra_log("SUCCESSO", "Magazzino resettato")
                        st.success("Magazzino resettato ai valori iniziali!")
                        st.rerun()

                with col_res2:
                    if st.button("🧹 Pulisci Log Movimenti", key="clean_logs"):
                        registra_log("PULIZIA", "Pulizia log movimenti magazzino")
                        log_file = "data/magazzino_log.csv"
                        if os.path.exists(log_file):
                            # Mantieni solo ultimi 1000 record
                            try:
                                df_log = pd.read_csv(log_file)
                                if len(df_log) > 1000:
                                    df_log = df_log.tail(1000)
                                    df_log.to_csv(log_file, index=False)
                                    registra_log("SUCCESSO", "Log pulito (mantenuti ultimi 1000 record)")
                                    st.success("Log pulito (mantenuti ultimi 1000 record)")
                                else:
                                    registra_log("INFO", "Log già sotto i 1000 record")
                                    st.info("Log già sotto i 1000 record")
                            except:
                                registra_log("ERRORE", "Errore pulizia log magazzino")
                                st.warning("Errore nella pulizia del log")

        with tab_info:
            st.subheader("Informazioni Sistema")

            # Usa la lingua dalle impostazioni per i messaggi
            lingua_attuale = st.session_state.impostazioni['lingua']

            col_info1, col_info2 = st.columns(2)

            with col_info1:
                st.metric("Versione Applicazione", "1.0.0")
                st.metric("Prodotti Caricati", len(analyzer.df_combinato))
                st.metric("Ingredienti Registrati", len(analyzer.df_magazzino))

                # Dimensione database
                total_size = 0
                data_files = ["data/bom.csv", "data/ciclo.csv", "data/magazzino.csv", "data/magazzino_log.csv"]
                for file in data_files:
                    if os.path.exists(file):
                        total_size += os.path.getsize(file)

                st.metric("Dimensione Dati", f"{total_size/1024:.1f} KB")
       
            with col_info2:
                st.metric("Ultimo Aggiornamento",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.metric("File Magazzino",
                         "✅ Presente" if os.path.exists("data/magazzino.csv") else "❌ Assente")
                st.metric("Log Movimenti",
                         "✅ Attivo" if os.path.exists("data/magazzino_log.csv") else "⚠️ Inattivo")

                # Stato sistema
                sistema_ok = all([
                    os.path.exists("data/bom.csv"),
                    os.path.exists("data/ciclo.csv"),
                    analyzer is not None
                ])

                if sistema_ok:
                    if lingua_attuale == "English":
                        st.success("✅ System Operational")
                    elif lingua_attuale == "Español":
                        st.success("✅ Sistema Operativo")
                    else:
                        st.success("✅ Sistema Operativo")
                else:
                    if lingua_attuale == "English":
                        st.error("❌ System with Problems")
                    elif lingua_attuale == "Español":
                        st.error("❌ Sistema con Problemas")
                    else:
                        st.error("❌ Sistema con Problemi")
       
            st.markdown("---")
            st.subheader("📁 File di Dati")

            files = [
                ("data/bom.csv", "Dati ingredienti", "Ingredienti per prodotto"),
                ("data/ciclo.csv", "Dati produzione", "Cicli di produzione"),
                ("data/magazzino.csv", "Stato magazzino", "Quantità ingredienti"),
                ("data/magazzino_log.csv", "Log movimenti", "Storico movimenti")
            ]

            for file_name, descrizione, dettaglio in files:
                with st.container():
                    col_file1, col_file2, col_file3, col_file4 = st.columns([3, 2, 1, 1])

                    with col_file1:
                        if lingua_attuale == "English":
                            if descrizione == "Dati ingredienti":
                                descrizione = "Ingredient Data"
                            elif descrizione == "Dati produzione":
                                descrizione = "Production Data"
                            elif descrizione == "Stato magazzino":
                                descrizione = "Warehouse Status"
                            elif descrizione == "Log movimenti":
                                descrizione = "Movement Logs"

                        st.write(f"**{descrizione}**")
                        st.caption(f"`{file_name}`")

                    with col_file2:
                        if os.path.exists(file_name):
                            file_size = os.path.getsize(file_name)
                            file_date = datetime.fromtimestamp(os.path.getmtime(file_name))
                            st.write(f"{file_size/1024:.1f} KB")
                            st.caption(f"Mod: {file_date.strftime('%d/%m/%Y')}")
                        else:
                            if lingua_attuale == "English":
                                st.error("Not found")
                            elif lingua_attuale == "Español":
                                st.error("No encontrado")
                            else:
                                st.error("Non presente")

                    with col_file3:
                        if os.path.exists(file_name):
                            if st.button("👁️", key=f"view_{file_name}", help="Anteprima"):
                                try:
                                    df = pd.read_csv(file_name)
                                    if lingua_attuale == "English":
                                        st.write(f"**Preview {descrizione}**")
                                    elif lingua_attuale == "Español":
                                        st.write(f"**Vista Previa {descrizione}**")
                                    else:
                                        st.write(f"**Anteprima {descrizione}**")
                                    st.dataframe(df.head(5), use_container_width=True)
                                except Exception as e:
                                    st.error(f"Errore lettura: {str(e)}")

                    with col_file4:
                        if os.path.exists(file_name):
                            with open(file_name, 'rb') as f:
                                file_data = f.read()
                            st.download_button(
                                label="📥",
                                data=file_data,
                                file_name=os.path.basename(file_name),
                                mime="text/csv",
                                key=f"dl_{file_name}"
                            )

            # Informazioni tecniche
            st.markdown("---")
            with st.expander("🔧 Informazioni Tecniche", expanded=False):
                if lingua_attuale == "English":
                    st.write(f"**Python Version:** {sys.version}")
                    st.write(f"**Pandas Version:** {pd.__version__}")
                    st.write(f"**Streamlit Version:** {st.__version__}")
                    st.write(f"**NumPy Version:** {np.__version__}")
                    st.write(f"**Plotly Version:** {plotly.__version__}")

                    # Memory usage - Gestione psutil opzionale
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_usage = process.memory_info().rss / 1024 / 1024
                        st.write(f"**Memory Usage:** {memory_usage:.1f} MB")
                    except ImportError:
                        st.write("**Memory Usage:** psutil not installed")
                    except Exception:
                        st.write("**Memory Usage:** Not available")
                elif lingua_attuale == "Español":
                    st.write(f"**Versión Python:** {sys.version}")
                    st.write(f"**Versión Pandas:** {pd.__version__}")
                    st.write(f"**Versión Streamlit:** {st.__version__}")
                    st.write(f"**Versión NumPy:** {np.__version__}")
                    st.write(f"**Versión Plotly:** {plotly.__version__}")

                    try:
                        import psutil
                        process = psutil.Process()
                        memory_usage = process.memory_info().rss / 1024 / 1024
                        st.write(f"**Uso de Memoria:** {memory_usage:.1f} MB")
                    except ImportError:
                        st.write("**Uso de Memoria:** psutil no instalado")
                    except Exception:
                        st.write("**Uso de Memoria:** No disponible")
                else:
                    st.write(f"**Python Version:** {sys.version}")
                    st.write(f"**Pandas Version:** {pd.__version__}")
                    st.write(f"**Streamlit Version:** {st.__version__}")
                    st.write(f"**NumPy Version:** {np.__version__}")
                    st.write(f"**Plotly Version:** {plotly.__version__}")
               
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_usage = process.memory_info().rss / 1024 / 1024
                        st.write(f"**Memory Usage:** {memory_usage:.1f} MB")
                    except ImportError:
                        st.write("**Memory Usage:** psutil non installato")
                    except Exception:
                        st.write("**Memory Usage:** Non disponibile")
   
        # ... (il resto del codice per la tab Backup & Ripristino rimane uguale)
    
    elif pagina == "📋 Log Sistema":
        st.header("📋 Log Sistema Completo")
        registra_log("PAGINA", "Accesso log sistema completo")
       
        if LOG_ATTIVO:
            st.success("✅ Sistema di log ATTIVATO - Tutti i movimenti vengono registrati")
        else:
            st.warning("⚠️ Sistema di log DISATTIVATO")
       
        if 'log_movimenti' in st.session_state and st.session_state.log_movimenti:
            # Converti in DataFrame per visualizzazione
            df_log = pd.DataFrame(st.session_state.log_movimenti)
           
            # Filtri log
            col1, col2, col3 = st.columns(3)
           
            with col1:
                tipi_log = df_log['tipo'].unique().tolist()
                tipo_filtro = st.multiselect("Filtra per tipo:", tipi_log, default=tipi_log)
           
            with col2:
                cerca_testo = st.text_input("Cerca nel log:", "")
           
            with col3:
                ordine = st.selectbox("Ordina per:", ["Più recenti prima", "Più vecchi prima"])
           
            # Applica filtri
            df_filtrato = df_log.copy()
           
            if tipo_filtro:
                df_filtrato = df_filtrato[df_filtrato['tipo'].isin(tipo_filtro)]
           
            if cerca_testo:
                df_filtrato = df_filtrato[
                    df_filtrato['descrizione'].str.contains(cerca_testo, case=False, na=False) |
                    df_filtrato['dettagli'].str.contains(cerca_testo, case=False, na=False)
                ]
           
            # Ordina
            if ordine == "Più recenti prima":
                df_filtrato = df_filtrato.sort_values('timestamp', ascending=False)
            else:
                df_filtrato = df_filtrato.sort_values('timestamp', ascending=True)
           
            # Mostra tabella
            st.dataframe(
                df_filtrato,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": st.column_config.TextColumn("Data/Ora", width="small"),
                    "tipo": st.column_config.TextColumn("Tipo", width="small"),
                    "descrizione": st.column_config.TextColumn("Descrizione", width="medium"),
                    "dettagli": st.column_config.TextColumn("Dettagli", width="large")
                }
            )
           
            # Statistiche
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
           
            with col_stat1:
                st.metric("Log Totali", len(df_log))
           
            with col_stat2:
                successi = len(df_log[df_log['tipo'] == 'SUCCESSO'])
                st.metric("Successi", successi)
           
            with col_stat3:
                errori = len(df_log[df_log['tipo'] == 'ERRORE'])
                st.metric("Errori", errori)
           
            with col_stat4:
                st.metric("Log Filtrati", len(df_filtrato))
           
            # Pulsanti azione
            col_btn1, col_btn2, col_btn3 = st.columns(3)
           
            with col_btn1:
                if st.button("🔄 Aggiorna Visualizzazione", key="refresh_logs_full"):
                    st.rerun()
           
            with col_btn2:
                if st.button("🗑️ Pulisci Tutti i Log", type="secondary", key="clear_all_logs_full"):
                    st.session_state.log_movimenti = []
                    registra_log("PULIZIA", "Tutti i log del sistema sono stati puliti")
                    st.rerun()
           
            with col_btn3:
                if st.button("📊 Statistiche Dettagliate", key="log_stats_full"):
                    registra_log("STATISTICHE", "Generazione statistiche dettagliate log")
                    st.subheader("📈 Statistiche Dettagliate Log")
                   
                    # Distribuzione temporale
                    df_log['ora'] = pd.to_datetime(df_log['timestamp']).dt.hour
                    distribuzione_ora = df_log['ora'].value_counts().sort_index()
                   
                    fig_dist = px.bar(x=distribuzione_ora.index, y=distribuzione_ora.values,
                                     title="Distribuzione Log per Ora del Giorno",
                                     labels={'x': 'Ora', 'y': 'Numero Log'})
                    st.plotly_chart(fig_dist, use_container_width=True)
                   
                    # Distribuzione per tipo
                    fig_tipo = px.pie(df_log, names='tipo', title="Distribuzione Log per Tipo")
                    st.plotly_chart(fig_tipo, use_container_width=True)
       
        else:
            st.info("📝 Nessun movimento registrato ancora. I log appariranno qui quando interagisci con l'applicazione.")

# Footer
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("Sistema di Analisi Produzione Panificio © 2024")

with footer_col2:
    st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with footer_col3:
    st.caption(f"Versioni: Streamlit {st.__version__} | Plotly {plotly.__version__} | Pandas {pd.__version__}")

# Log finale
registra_log("SISTEMA", "Applicazione pronta", "Stato: Attivo, Log: Attivo")