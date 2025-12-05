import streamlit as st
from app import load_data, chart_pareto, chart_scatter_zipf, chart_violin

# Charger les données (filtrées dans app.py)
df_viz = load_data()

st.title("📊 STATISTIQUES AVANCÉES")

if df_viz is not None and not df_viz.empty:
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_pareto(df_viz), use_container_width=True)
        st.caption("💡 **Loi de Pareto** : Vérifiez si 20% des stations génèrent 80% du trafic.")
    with c2:
        st.plotly_chart(chart_scatter_zipf(df_viz), use_container_width=True)
        st.caption("💡 **Loi de Zipf** : Une ligne droite indique une distribution de puissance parfaite.")
    
    st.plotly_chart(chart_violin(df_viz), use_container_width=True)

else:
    st.warning("Aucune donnée à afficher pour les filtres sélectionnés. Veuillez ajuster le 'Centre de Contrôle' sur la page d'accueil.")
