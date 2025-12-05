import streamlit as st
from app import load_data

# Charger les données (filtrées dans app.py)
df_viz = load_data()

st.title("💾 DONNÉES BRUTES")

if df_viz is not None and not df_viz.empty:
    
    st.dataframe(
        df_viz[['Rang', 'Reseau', 'Station', 'Ville', 'Trafic']].sort_values('Rang'),
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Aucune donnée à afficher pour les filtres sélectionnés. Veuillez ajuster le 'Centre de Contrôle' sur la page d'accueil.")
