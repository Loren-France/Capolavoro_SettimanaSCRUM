import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from forecast_module import load_forecaster

def show_forecast_dashboard():
    """Mostra dashboard di previsione della domanda"""
    st.header("🔮 Previsioni di Mercato - Analisi Dati Storici")
    
    # Metriche introduttive
    with st.spinner("🔄 Caricamento dati di vendita storici (645k+ record)..."):
        forecaster = load_forecaster()
    
    if forecaster is None or len(forecaster.combined_data) == 0:
        st.error("❌ Impossibile caricare i dati di previsione.")
        st.info("Verifica che i file CSV siano presenti nella cartella 'data/'")
        return
    
    # Statistiche dataset
    total_rows = len(forecaster.combined_data)
    unique_products = forecaster.combined_data['nome_pane'].nunique()
    weeks_covered = forecaster.combined_data['week'].nunique()
    total_orders = forecaster.combined_data['num_orders'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Record Storici", f"{total_rows:,}", help="Totale righe nel dataset")
    with col2:
        st.metric("Prodotti Unici", unique_products, help="Prodotti diversi analizzati")
    with col3:
        st.metric("Settimane Dati", weeks_covered, help="Settimane di dati storici")
    with col4:
        st.metric("Ordini Totali", f"{total_orders:,}", help="Ordini storici totali")
    
    st.markdown("---")
    
    # Tab principale
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Previsione Prodotto", 
        "📈 Analisi Trend", 
        "🏆 Top Prodotti",
        "📋 Report Completo"
    ])
    
    with tab1:
        show_product_forecast_tab(forecaster)
    
    with tab2:
        show_trend_analysis_tab(forecaster)
    
    with tab3:
        show_top_products_tab(forecaster)
    
    with tab4:
        show_complete_report_tab(forecaster)

def show_product_forecast_tab(forecaster):
    """Tab per previsione singolo prodotto"""
    st.subheader("🎯 Previsione Domanda per Prodotto")
    
    # Seleziona prodotto
    available_products = forecaster.combined_data['nome_pane'].dropna().unique()
    
    if len(available_products) == 0:
        st.warning("Nessun prodotto disponibile nei dati.")
        return
    
    # Cerca prodotto
    search_term = st.text_input("🔍 Cerca prodotto:", placeholder="Digita nome prodotto...")
    
    if search_term:
        filtered_products = [p for p in available_products if search_term.lower() in p.lower()]
    else:
        filtered_products = list(available_products[:100])  # Limita a 100 per performance
    
    selected_product = st.selectbox(
        "Seleziona prodotto:",
        filtered_products,
        index=0 if filtered_products else None,
        help="Scegli un prodotto per analizzare e prevedere la domanda"
    )
    
    if selected_product:
        # Ottieni ID prodotto
        product_data = forecaster.combined_data[
            forecaster.combined_data['nome_pane'] == selected_product
        ]
        
        if product_data.empty:
            st.error("Prodotto non trovato.")
            return
        
        product_id = product_data['meal_id'].iloc[0]
        
        # Statistiche prodotto
        stats = forecaster.get_product_stats(product_name=selected_product)
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Ordini Totali", f"{stats.get('total_orders', 0):,}")
        with col_stat2:
            st.metric("Media Settimanale", f"{stats.get('avg_weekly_orders', 0):.0f}")
        with col_stat3:
            st.metric("Settimane Dati", stats.get('weeks_of_data', 0))
        
        # Parametri previsione
        with st.expander("⚙️ Parametri Previsione", expanded=True):
            col_param1, col_param2, col_param3 = st.columns(3)
            
            with col_param1:
                weeks_ahead = st.slider("Settimane da prevedere:", 1, 12, 4, 
                                      help="Numero di settimane future da prevedere")
            
            with col_param2:
                center_id = st.selectbox("Centro vendita:", 
                                       sorted(forecaster.combined_data['center_id'].unique()),
                                       index=0,
                                       help="Seleziona il centro vendita")
            
            with col_param3:
                promo_scenario = st.selectbox("Scenario promozionale:",
                                            ["Nessuna promozione", "Promozione leggera", "Promozione forte"],
                                            index=0,
                                            help="Imposta lo scenario promozionale")
        
        # Pulsante previsione
        if st.button("🚀 Genera Previsione", type="primary", use_container_width=True):
            with st.spinner("🎯 Calcolando previsione..."):
                try:
                    # Genera previsione
                    forecast_df = forecaster.forecast_demand(
                        product_id=product_id,
                        weeks_ahead=weeks_ahead,
                        center_id=center_id
                    )
                    
                    if forecast_df.empty:
                        st.warning("Impossibile generare previsione.")
                        return
                    
                    # Mostra risultati
                    st.success(f"✅ Previsione generata per {selected_product}")
                    
                    # Metriche previsione
                    col_pred1, col_pred2, col_pred3 = st.columns(3)
                    with col_pred1:
                        total_pred = forecast_df['predicted_orders'].sum()
                        st.metric("Ordini Previsti Totali", f"{int(total_pred):,}")
                    with col_pred2:
                        avg_pred = forecast_df['predicted_orders'].mean()
                        st.metric("Media Settimanale", f"{avg_pred:.0f}")
                    with col_pred3:
                        st.metric("Produzione Stimata (kg)", f"{int(total_pred * 2):,}")
                    
                    # Grafico previsione
                    fig = go.Figure()
                    
                    # Dati storici (ultime 8 settimane)
                    historical = product_data.sort_values('week').tail(8)
                    
                    fig.add_trace(go.Bar(
                        x=historical['week'],
                        y=historical['num_orders'],
                        name='Storico',
                        marker_color='lightblue',
                        opacity=0.7
                    ))
                    
                    # Previsioni
                    fig.add_trace(go.Scatter(
                        x=forecast_df['week'],
                        y=forecast_df['predicted_orders'],
                        mode='lines+markers',
                        name='Previsione',
                        line=dict(color='red', width=3),
                        marker=dict(size=10)
                    ))
                    
                    fig.update_layout(
                        title=f"Previsione Domanda: {selected_product}",
                        xaxis_title="Settimana",
                        yaxis_title="Numero Ordini",
                        hovermode='x unified',
                        showlegend=True,
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabella dettagliata
                    with st.expander("📋 Dettaglio Settimanale"):
                        display_df = forecast_df[['week', 'week_date', 'predicted_orders', 
                                                 'predicted_kg', 'checkout_price', 'confidence']].copy()
                        display_df.columns = ['Settimana', 'Data', 'Ordini Previsti', 
                                            'Kg Previsti', 'Prezzo (€)', 'Confidenza']
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            column_config={
                                "Settimana": st.column_config.NumberColumn(format="%d"),
                                "Ordini Previsti": st.column_config.NumberColumn(format="%d"),
                                "Kg Previsti": st.column_config.NumberColumn(format="%d kg"),
                                "Prezzo (€)": st.column_config.NumberColumn(format="€%.2f")
                            }
                        )
                    
                    # Raccomandazioni
                    st.subheader("💡 Raccomandazioni Produzione")
                    
                    recommendations = []
                    
                    if total_pred > stats.get('avg_weekly_orders', 0) * weeks_ahead * 1.2:
                        recommendations.append("📈 **Aumenta produzione**: Domanda prevista superiore alla media storica")
                        recommendations.append("   • Pianifica turni aggiuntivi")
                        recommendations.append("   • Verifica disponibilità ingredienti")
                    
                    elif total_pred < stats.get('avg_weekly_orders', 0) * weeks_ahead * 0.8:
                        recommendations.append("📉 **Riduci produzione**: Domanda prevista inferiore alla media")
                        recommendations.append("   • Valuta promozioni per stimolare vendite")
                        recommendations.append("   • Rivedi piani di produzione")
                    
                    else:
                        recommendations.append("⚖️ **Mantieni produzione**: Domanda in linea con le attese")
                        recommendations.append("   • Continua con livelli produttivi attuali")
                        recommendations.append("   • Monitora andamento settimanale")
                    
                    for rec in recommendations:
                        st.write(rec)
                    
                    # Export dati
                    if st.button("📥 Esporta Previsioni CSV"):
                        csv = forecast_df.to_csv(index=False)
                        st.download_button(
                            label="Scarica CSV",
                            data=csv,
                            file_name=f"previsione_{selected_product}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                except Exception as e:
                    st.error(f"Errore nella previsione: {str(e)}")

def show_trend_analysis_tab(forecaster):
    """Tab per analisi trend"""
    st.subheader("📈 Analisi Trend e Stagionalità")
    
    # Seleziona prodotto per analisi
    top_products = forecaster.get_top_products(20)
    
    if len(top_products) == 0:
        st.warning("Nessun prodotto disponibile per l'analisi.")
        return
    
    selected_product = st.selectbox(
        "Prodotto per analisi trend:",
        top_products['nome_pane'].tolist(),
        index=0,
        key="trend_product_select"
    )
    
    if selected_product:
        product_id = top_products[top_products['nome_pane'] == selected_product]['meal_id'].iloc[0]
        
        # Analisi stagionalità
        with st.spinner("Analizzando trend..."):
            seasonality = forecaster.analyze_seasonality(product_id)
            stats = forecaster.get_product_stats(product_id=product_id)
        
        if not seasonality:
            st.warning("Analisi non disponibile per questo prodotto.")
            return
        
        # Metriche trend
        col_trend1, col_trend2, col_trend3 = st.columns(3)
        
        with col_trend1:
            trend_direction = seasonality.get('trend_direction', 'Stabile')
            trend_color = "green" if trend_direction == "Crescente" else "red" if trend_direction == "Decrescente" else "gray"
            st.metric("Direzione Trend", trend_direction)
        
        with col_trend2:
            seasonality_score = seasonality.get('seasonality_score', 'N/A')
            st.metric("Stagionalità", seasonality_score)
        
        with col_trend3:
            st.metric("Stabilità Dati", 
                     stats.get('confidence', 'N/A'),
                     help="Basato sulla variabilità dei dati storici")
        
        # Grafico pattern stagionale
        if 'weekly_pattern' in seasonality and seasonality['weekly_pattern']:
            pattern_df = pd.DataFrame(seasonality['weekly_pattern'])
            
            fig = px.line(
                pattern_df,
                x='week_of_year',
                y='media_ordini',
                title=f"Pattern Stagionale: {selected_product}",
                labels={'week_of_year': 'Settimana dell\'anno', 'media_ordini': 'Ordini Medi'},
                markers=True
            )
            
            # Aggiungi area
            fig.add_trace(go.Scatter(
                x=pattern_df['week_of_year'],
                y=pattern_df['media_ordini'],
                fill='tozeroy',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False
            ))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Insight dall'analisi
        st.subheader("🔍 Insight dall'Analisi")
        
        insights = []
        
        trend_slope = seasonality.get('trend_slope', 0)
        if abs(trend_slope) > 0.2:
            if trend_slope > 0:
                insights.append("✅ **Trend positivo**: La domanda mostra crescita costante")
                insights.append(f"   • Incremento medio: {trend_slope:.2f} ordini per settimana")
                insights.append("   • Opportunità per espansione produzione")
            else:
                insights.append("⚠️ **Trend negativo**: Attenzione alla domanda in calo")
                insights.append(f"   • Decremento medio: {abs(trend_slope):.2f} ordini per settimana")
                insights.append("   • Valuta strategie di rilancio")
        else:
            insights.append("📊 **Trend stabile**: La domanda è consistente")
            insights.append("   • Poca variabilità nelle vendite")
            insights.append("   • Produzione prevedibile e pianificabile")
        
        # Consigli specifici
        st.subheader("🎯 Consigli Operativi")
        
        if seasonality_score == "Alta stagionalità":
            st.info("""
            **Pianificazione stagionale richiesta:**
            - Identifica periodi di picco e prepara scorte in anticipo
            - Considera produzione extra 2-3 settimane prima dei picchi attesi
            - Pianifica turni supplementari per i periodi di alta domanda
            """)
        elif stats.get('recent_trend', 0) > 5:
            st.success("""
            **Crescita in atto:**
            - Valuta aumento capacità produttiva
            - Assicura forniture ingredienti a lungo termine
            - Monitora costantemente la domanda per evitare stockout
            """)
        else:
            st.info("""
            **Operatività standard:**
            - Mantieni livelli produttivi attuali
            - Monitora indicatori chiave settimanalmente
            - Prepara piani contingenza per variazioni improvvise
            """)

def show_top_products_tab(forecaster):
    """Tab per top prodotti"""
    st.subheader("🏆 Classifica Prodotti più Venduti")
    
    # Numero prodotti da mostrare
    n_products = st.slider("Numero prodotti in classifica:", 5, 50, 15)
    
    with st.spinner("Generando classifica..."):
        top_products = forecaster.get_top_products(n_products)
    
    if len(top_products) == 0:
        st.warning("Nessun dato disponibile.")
        return
    
    # Grafico a barre top prodotti
    fig = px.bar(
        top_products,
        x='nome_pane',
        y='ordini_totali',
        title=f"Top {n_products} Prodotti per Vendite Totali",
        labels={'nome_pane': 'Prodotto', 'ordini_totali': 'Ordini Totali'},
        color='ordini_totali',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabella dettagliata
    with st.expander("📋 Dettaglio Prodotti"):
        display_df = top_products.copy()
        display_df['ordini_settimanali_medi'] = display_df['ordini_totali'] / display_df['settimane_dati']
        display_df = display_df.round({'ordini_settimanali_medi': 0})
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "nome_pane": "Prodotto",
                "ordini_totali": st.column_config.NumberColumn(
                    "Ordini Totali",
                    format="%,d"
                ),
                "settimane_dati": st.column_config.NumberColumn(
                    "Settimane Dati",
                    format="%d"
                ),
                "ordini_settimanali_medi": st.column_config.NumberColumn(
                    "Media Settimanale",
                    format="%.0f"
                )
            },
            hide_index=True
        )
    
    # Confronto previsioni top prodotti
    st.subheader("📊 Confronto Previsioni Top Prodotti")
    
    if st.button("🔮 Confronta Previsioni", type="secondary"):
        with st.spinner("Calcolando previsioni comparative..."):
            # Prendi top 5 prodotti
            top_5_ids = top_products.head(5)['meal_id'].tolist()
            top_5_names = top_products.head(5)['nome_pane'].tolist()
            
            comparisons = forecaster.compare_products(top_5_ids, weeks_ahead=4)
            
            if not comparisons.empty:
                # Grafico confronto
                fig2 = px.bar(
                    comparisons,
                    x='product_name',
                    y='total_predicted',
                    title='Confronto Previsioni 4 Settimane',
                    labels={'product_name': 'Prodotto', 'total_predicted': 'Ordini Previsti'},
                    color='total_predicted',
                    color_continuous_scale='RdYlGn'
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Insight
                st.subheader("💡 Insight dal Confronto")
                
                best_product = comparisons.loc[comparisons['total_predicted'].idxmax()]
                worst_product = comparisons.loc[comparisons['total_predicted'].idxmin()]
                
                col_insight1, col_insight2 = st.columns(2)
                
                with col_insight1:
                    st.success(f"**Migliore performance:** {best_product['product_name']}")
                    st.write(f"- Ordini previsti: {best_product['total_predicted']:,}")
                    st.write(f"- Media settimanale: {best_product['avg_predicted']:.0f}")
                    st.write(f"- Livello confidenza: {best_product['confidence']}")
                
                with col_insight2:
                    st.warning(f"**Performance più bassa:** {worst_product['product_name']}")
                    st.write(f"- Ordini previsti: {worst_product['total_predicted']:,}")
                    st.write(f"- Media settimanale: {worst_product['avg_predicted']:.0f}")
                    st.write(f"- Livello confidenza: {worst_product['confidence']}")

def show_complete_report_tab(forecaster):
    """Tab per report completo"""
    st.subheader("📋 Report Analisi Mercato Completo")
    
    st.info("Genera un report completo basato sui dati storici di vendita.")
    
    # Seleziona tipo di report
    report_type = st.radio(
        "Tipo di report:",
        ["📊 Panoramica Mercato", "🎯 Analisi per Prodotto", "📈 Trend Globali"],
        horizontal=True
    )
    
    if report_type == "📊 Panoramica Mercato":
        show_market_overview(forecaster)
    elif report_type == "🎯 Analisi per Prodotto":
        show_product_analysis_report(forecaster)
    elif report_type == "📈 Trend Globali":
        show_global_trends_report(forecaster)

def show_market_overview(forecaster):
    """Mostra panoramica del mercato"""
    if st.button("📊 Genera Report Panoramica", type="primary"):
        with st.spinner("Analizzando dati di mercato..."):
            try:
                # Calcola metriche mercato
                total_orders = forecaster.combined_data['num_orders'].sum()
                avg_weekly_orders = forecaster.combined_data.groupby('week')['num_orders'].sum().mean()
                peak_week = forecaster.combined_data.groupby('week')['num_orders'].sum().idxmax()
                peak_orders = forecaster.combined_data.groupby('week')['num_orders'].sum().max()
                
                top_10_products = forecaster.get_top_products(10)
                top_product = top_10_products.iloc[0]
                
                # Metriche
                col_rep1, col_rep2, col_rep3, col_rep4 = st.columns(4)
                
                with col_rep1:
                    st.metric("Ordini Totali Mercato", f"{total_orders:,}")
                
                with col_rep2:
                    st.metric("Media Settimanale", f"{avg_weekly_orders:,.0f}")
                
                with col_rep3:
                    st.metric("Settimana Picco", f"Week {peak_week}", f"{peak_orders:,} ordini")
                
                with col_rep4:
                    st.metric("Prodotto Top", top_product['nome_pane'], f"{top_product['ordini_totali']:,} ordini")
                
                # Distribuzione ordini per settimana
                weekly_dist = forecaster.combined_data.groupby('week')['num_orders'].sum().reset_index()
                
                fig = px.line(
                    weekly_dist,
                    x='week',
                    y='num_orders',
                    title='Andamento Ordini Settimanali - Mercato Totale',
                    labels={'num_orders': 'Ordini Totali', 'week': 'Settimana'},
                    markers=True
                )
                
                # Aggiungi media
                fig.add_hline(y=avg_weekly_orders, line_dash="dash", 
                            annotation_text=f"Media: {avg_weekly_orders:,.0f}")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Insight mercato
                st.subheader("🔍 Insight Mercato")
                
                st.write("**Performance Mercato:**")
                
                # Calcola crescita
                if len(weekly_dist) > 4:
                    recent_avg = weekly_dist.tail(4)['num_orders'].mean()
                    previous_avg = weekly_dist.iloc[-8:-4]['num_orders'].mean() if len(weekly_dist) > 8 else recent_avg
                    
                    growth = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
                    
                    if growth > 5:
                        st.success(f"📈 **Mercato in crescita**: +{growth:.1f}% nelle ultime 4 settimane")
                    elif growth < -5:
                        st.warning(f"📉 **Mercato in contrazione**: {growth:.1f}% nelle ultime 4 settimane")
                    else:
                        st.info(f"📊 **Mercato stabile**: Variazione {growth:.1f}% nelle ultime 4 settimane")
                
                # Raccomandazioni strategiche
                st.subheader("🎯 Raccomandazioni Strategiche")
                
                recommendations = [
                    "**Pianificazione Produzione:**",
                    "• Allinea produzione con trend settimanali identificati",
                    "• Prepara buffer produzione per settimane di picco",
                    "",
                    "**Gestione Magazzino:**",
                    "• Ottimizza scorte basate su stagionalità prodotto",
                    "• Monitora ingredienti critici per prodotti top",
                    "",
                    "**Strategia Vendite:**",
                    "• Concentra promozioni su prodotti con trend positivo",
                    "• Valuta bundle prodotti complementari"
                ]
                
                for rec in recommendations:
                    if rec.startswith("**"):
                        st.markdown(f"**{rec[2:]}**")
                    elif rec:
                        st.write(f"   {rec}")
                
            except Exception as e:
                st.error(f"Errore nella generazione del report: {str(e)}")

def show_product_analysis_report(forecaster):
    """Mostra report analisi prodotto"""
    # Seleziona prodotto
    top_products = forecaster.get_top_products(30)
    
    if len(top_products) == 0:
        st.warning("Nessun prodotto disponibile.")
        return
    
    selected_product = st.selectbox(
        "Seleziona prodotto per report dettagliato:",
        top_products['nome_pane'].tolist(),
        index=0,
        key="report_product"
    )
    
    if selected_product and st.button("📄 Genera Report Prodotto", type="primary"):
        with st.spinner("Generando report prodotto..."):
            try:
                product_id = top_products[top_products['nome_pane'] == selected_product]['meal_id'].iloc[0]
                
                # Ottieni tutte le analisi
                stats = forecaster.get_product_stats(product_id=product_id)
                seasonality = forecaster.analyze_seasonality(product_id)
                forecast = forecaster.forecast_demand(product_id, weeks_ahead=4)
                
                # Header report
                st.markdown(f"## 📋 Report Analisi: {selected_product}")
                st.markdown(f"*Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
                
                # Sezione 1: Statistiche Storiche
                st.subheader("📊 Statistiche Storiche")
                
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                
                with col_s1:
                    st.metric("Ordini Totali", f"{stats.get('total_orders', 0):,}")
                
                with col_s2:
                    st.metric("Media Settimanale", f"{stats.get('avg_weekly_orders', 0):.0f}")
                
                with col_s3:
                    st.metric("Massimo Storico", stats.get('max_weekly_orders', 0))
                
                with col_s4:
                    st.metric("Settimane Dati", stats.get('weeks_of_data', 0))
                
                # Sezione 2: Previsioni
                if not forecast.empty:
                    st.subheader("🔮 Previsioni 4 Settimane")
                    
                    col_f1, col_f2, col_f3 = st.columns(3)
                    
                    with col_f1:
                        total_pred = forecast['predicted_orders'].sum()
                        st.metric("Ordini Previsti", f"{int(total_pred):,}")
                    
                    with col_f2:
                        kg_pred = forecast['predicted_kg'].sum()
                        st.metric("Produzione Stimata", f"{int(kg_pred):,} kg")
                    
                    with col_f3:
                        st.metric("Livello Confidenza", forecast['confidence'].iloc[0])
                    
                    # Tabella previsioni dettagliate
                    with st.expander("📅 Dettaglio Previsioni Settimanali"):
                        display_forecast = forecast[['week', 'week_date', 'predicted_orders', 
                                                    'predicted_kg', 'confidence']].copy()
                        display_forecast.columns = ['Settimana', 'Data', 'Ordini Previsti', 
                                                  'Kg Previsti', 'Confidenza']
                        
                        st.dataframe(display_forecast, use_container_width=True)
                
                # Sezione 3: Analisi Trend
                st.subheader("📈 Analisi Trend")
                
                if seasonality:
                    col_t1, col_t2 = st.columns(2)
                    
                    with col_t1:
                        st.metric("Direzione Trend", seasonality.get('trend_direction', 'N/A'))
                    
                    with col_t2:
                        st.metric("Stagionalità", seasonality.get('seasonality_score', 'N/A'))
                    
                    # Pattern stagionale
                    if 'weekly_pattern' in seasonality and seasonality['weekly_pattern']:
                        pattern_df = pd.DataFrame(seasonality['weekly_pattern'])
                        
                        fig = px.line(
                            pattern_df,
                            x='week_of_year',
                            y='media_ordini',
                            title='Pattern Stagionale',
                            labels={'week_of_year': 'Settimana dell\'anno', 'media_ordini': 'Ordini Medi'}
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Sezione 4: Raccomandazioni
                st.subheader("💡 Raccomandazioni Operative")
                
                recommendations = []
                
                # Basato su trend
                if seasonality.get('trend_direction') == 'Crescente':
                    recommendations.append("✅ **Aumenta capacità produttiva** per soddisfare domanda crescente")
                elif seasonality.get('trend_direction') == 'Decrescente':
                    recommendations.append("⚠️ **Rivedi strategia prodotto** per invertire trend negativo")
                
                # Basato su stagionalità
                if seasonality.get('seasonality_score') == 'Alta stagionalità':
                    recommendations.append("📅 **Pianifica produzione stagionale** per ottimizzare risorse")
                
                # Basato su previsioni
                if not forecast.empty:
                    avg_forecast = forecast['predicted_orders'].mean()
                    if avg_forecast > stats.get('avg_weekly_orders', 0) * 1.2:
                        recommendations.append("⚡ **Prepara scorte extra** per domanda prevista superiore")
                    elif avg_forecast < stats.get('avg_weekly_orders', 0) * 0.8:
                        recommendations.append("📉 **Riduci produzione base** e valuta promozioni")
                
                for rec in recommendations:
                    st.info(rec)
                
                # Export report
                st.subheader("📥 Esporta Report")
                
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    if st.button("💾 Salva Report CSV"):
                        # Crea CSV combinato
                        report_data = {
                            'prodotto': selected_product,
                            'meal_id': product_id,
                            'data_report': datetime.now().strftime('%Y-%m-%d'),
                            'ordini_totali': stats.get('total_orders', 0),
                            'media_settimanale': stats.get('avg_weekly_orders', 0),
                            'trend_direction': seasonality.get('trend_direction', 'N/A'),
                            'stagionalita': seasonality.get('seasonality_score', 'N/A')
                        }
                        
                        report_df = pd.DataFrame([report_data])
                        csv = report_df.to_csv(index=False)
                        
                        st.download_button(
                            label="Scarica CSV",
                            data=csv,
                            file_name=f"report_{selected_product}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                
                with col_exp2:
                    if st.button("🖨️ Stampa Sintesi"):
                        st.success("Funzionalità di stampa in sviluppo")
                
            except Exception as e:
                st.error(f"Errore nella generazione del report: {str(e)}")

def show_global_trends_report(forecaster):
    """Mostra report trend globali"""
    st.info("Analisi dei trend di mercato su tutti i prodotti.")
    
    if st.button("🌍 Analizza Trend Globali", type="primary"):
        with st.spinner("Analizzando trend di mercato..."):
            try:
                # Analizza top 20 prodotti
                top_20 = forecaster.get_top_products(20)
                
                if len(top_20) == 0:
                    st.warning("Nessun dato disponibile.")
                    return
                
                # Calcola trend per ogni prodotto
                trends = []
                
                for _, product in top_20.iterrows():
                    seasonality = forecaster.analyze_seasonality(product['meal_id'])
                    
                    if seasonality:
                        trends.append({
                            'prodotto': product['nome_pane'],
                            'ordini_totali': product['ordini_totali'],
                            'trend_direction': seasonality.get('trend_direction', 'Stabile'),
                            'stagionalita': seasonality.get('seasonality_score', 'N/A'),
                            'trend_slope': seasonality.get('trend_slope', 0)
                        })
                
                trends_df = pd.DataFrame(trends)
                
                # Analisi aggregata
                growing_products = len(trends_df[trends_df['trend_direction'] == 'Crescente'])
                declining_products = len(trends_df[trends_df['trend_direction'] == 'Decrescente'])
                stable_products = len(trends_df[trends_df['trend_direction'] == 'Stabile'])
                
                # Metriche globali
                col_g1, col_g2, col_g3 = st.columns(3)
                
                with col_g1:
                    st.metric("Prodotti in Crescita", growing_products, 
                            delta=f"{(growing_products/len(trends_df)*100):.0f}%")
                
                with col_g2:
                    st.metric("Prodotti Stabili", stable_products,
                            delta=f"{(stable_products/len(trends_df)*100):.0f}%")
                
                with col_g3:
                    st.metric("Prodotti in Calo", declining_products,
                            delta=f"{(declining_products/len(trends_df)*100):.0f}%",
                            delta_color="inverse")
                
                # Grafico distribuzione trend
                trend_dist = trends_df['trend_direction'].value_counts().reset_index()
                trend_dist.columns = ['trend', 'count']
                
                fig = px.pie(
                    trend_dist,
                    values='count',
                    names='trend',
                    title='Distribuzione Trend Prodotti Top 20',
                    color='trend',
                    color_discrete_map={
                        'Crescente': 'green',
                        'Stabile': 'gray',
                        'Decrescente': 'red'
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Insight globali
                st.subheader("🔍 Insight Trend Globali")
                
                if growing_products > declining_products * 2:
                    st.success("**📈 Mercato in forte crescita**")
                    st.write("• La maggior parte dei prodotti mostra trend positivo")
                    st.write("• Opportunità per espansione e nuovi investimenti")
                elif growing_products > declining_products:
                    st.info("**📊 Mercato in moderata crescita**")
                    st.write("• Bilancio positivo con più prodotti in crescita")
                    st.write("• Mantenere strategie attuali con monitoraggio")
                elif declining_products > growing_products:
                    st.warning("**⚠️ Mercato in contrazione**")
                    st.write("• Più prodotti in calo che in crescita")
                    st.write("• Valutare strategie di rilancio e diversificazione")
                else:
                    st.info("**⚖️ Mercato bilanciato**")
                    st.write("• Equilibrio tra prodotti in crescita e calo")
                    st.write("• Strategia differenziata per tipologia prodotto")
                
                # Tabella prodotti per trend
                with st.expander("📋 Dettaglio Prodotti per Trend"):
                    st.write("**Prodotti in Forte Crescita:**")
                    growing_df = trends_df[trends_df['trend_slope'] > 0.3].sort_values('trend_slope', ascending=False)
                    
                    if not growing_df.empty:
                        st.dataframe(
                            growing_df[['prodotto', 'ordini_totali', 'trend_direction', 'stagionalita']],
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    st.write("**Prodotti in Forte Calo:**")
                    declining_df = trends_df[trends_df['trend_slope'] < -0.3].sort_values('trend_slope')
                    
                    if not declining_df.empty:
                        st.dataframe(
                            declining_df[['prodotto', 'ordini_totali', 'trend_direction', 'stagionalita']],
                            use_container_width=True,
                            hide_index=True
                        )
                
            except Exception as e:
                st.error(f"Errore nell'analisi dei trend globali: {str(e)}")