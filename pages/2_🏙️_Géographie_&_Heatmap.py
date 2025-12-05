import streamlit as st
import plotly.express as px
from app import load_data, PLOT_THEME, chart_heatmap, COLOR_TREEMAP_END

# Charger les données (filtrées dans app.py)
df_viz = load_data()

st.title("🏙️ GÉOGRAPHIE & HEATMAP")

if df_viz is not None and not df_viz.empty:
    
    col_geo1, col_geo2 = st.columns([2, 1])
    with col_geo1:
        st.plotly_chart(chart_heatmap(df_viz), use_container_width=True)
    with col_geo2:
        # Treemap villes
        top_villes = df_viz.groupby('Ville')['Trafic'].sum().reset_index().nlargest(20, 'Trafic')
        fig_tree = px.treemap(
            top_villes, path=['Ville'], values='Trafic',
            color='Trafic', 
            color_continuous_scale=[(0, "white"), (1, COLOR_TREEMAP_END)],
            title="🏙️ Poids des Villes (Top 20)",
            template=PLOT_THEME
        )
        st.plotly_chart(fig_tree, use_container_width=True)

else:
    st.warning("Aucune donnée à afficher pour les filtres sélectionnés. Veuillez ajuster le 'Centre de Contrôle' sur la page d'accueil.")
