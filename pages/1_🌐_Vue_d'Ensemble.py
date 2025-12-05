import streamlit as st
import plotly.express as px
from app import load_data, PLOTLY_COLOR_MAP, PLOT_THEME, chart_sunburst, chart_bar_race

# Charger les données (filtrées dans app.py)
df_viz = load_data()

st.title("🌐 VUE D'ENSEMBLE")

if df_viz is not None and not df_viz.empty:
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(chart_sunburst(df_viz), use_container_width=True)
    with col2:
        st.plotly_chart(chart_bar_race(df_viz), use_container_width=True)
    
    # Jauge de répartition (Donut)
    st.plotly_chart(px.pie(
        df_viz, values='Trafic', names='Reseau', hole=0.5,
        color='Reseau', 
        color_discrete_map=PLOTLY_COLOR_MAP, 
        title="🍩 Répartition du Trafic par Réseau",
        template=PLOT_THEME
    ), use_container_width=True)

else:
    st.warning("Aucune donnée à afficher pour les filtres sélectionnés. Veuillez ajuster le 'Centre de Contrôle' sur la page d'accueil.")
