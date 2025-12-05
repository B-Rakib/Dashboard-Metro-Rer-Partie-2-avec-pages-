import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import toml 

# --- 1. CONFIGURATION & THEME ---
# La configuration du thème (couleurs de l'interface) est maintenant dans .streamlit/config.toml
st.set_page_config(
    page_title="RATP 360° - Thème Classique",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CONSTANTES (Lecture de config.toml) ---
FILE_PATH = r"Z:\RATP\trafic-annuel-entrant-par-station-du-reseau-ferre-2021.csv"

# Lecture de la palette Plotly à partir du fichier config.toml
try:
    config_path = os.path.join(".streamlit", "config.toml")
    with open(config_path, 'r') as f:
        config = toml.load(f)
    
    # Définition des constantes de couleurs à partir du TOML
    if 'colors' in config and 'theme' in config:
        PLOTLY_COLOR_MAP = {
            "Métro": config['colors']['metro'],
            "RER": config['colors']['rer'],
            "Tramway": config['colors']['tramway'],
            "Val": config['colors']['val'],
            "Inconnu": config['colors']['unknown'],
            "Autre": config['colors']['other']
        }
        COLOR_PARETO_LINE = config['colors']['metro'] 
        hex_color = COLOR_PARETO_LINE.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        COLOR_PARETO_FILL = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.3)" 
        COLOR_PARETO_80_20 = config['theme']['primaryColor'] 
        COLOR_HEATMAP_END = config['theme']['primaryColor'] 
        COLOR_TREEMAP_END = config['colors']['metro'] 
        
    else:
        st.error("Sections [colors] ou [theme] introuvables. Utilisation des couleurs par défaut.")
        # FALLBACK
        PLOTLY_COLOR_MAP = {
            "Métro": "#4bc0ad", "RER": "#e10b1a", "Tramway": "#6fa832", "Val": "#3a87ad", "Inconnu": "#95a5a6", "Autre": "#6c7a89"
        }
        COLOR_PARETO_LINE = PLOTLY_COLOR_MAP["Métro"]
        COLOR_PARETO_FILL = 'rgba(75, 192, 173, 0.3)'
        COLOR_PARETO_80_20 = "#004fa3"
        COLOR_HEATMAP_END = "#004fa3"
        COLOR_TREEMAP_END = PLOTLY_COLOR_MAP["Métro"]
        
except FileNotFoundError:
    st.error("Fichier .streamlit/config.toml introuvable. Utilisation des couleurs par défaut.")
    # FALLBACK
    PLOTLY_COLOR_MAP = {
        "Métro": "#4bc0ad", "RER": "#e10b1a", "Tramway": "#6fa832", "Val": "#3a87ad", "Inconnu": "#95a5a6", "Autre": "#6c7a89"
    }
    COLOR_PARETO_LINE = PLOTLY_COLOR_MAP["Métro"]
    COLOR_PARETO_FILL = 'rgba(75, 192, 173, 0.3)'
    COLOR_PARETO_80_20 = "#004fa3"
    COLOR_HEATMAP_END = "#004fa3"
    COLOR_TREEMAP_END = PLOTLY_COLOR_MAP["Métro"]

PLOT_THEME = "plotly_white"

# --- 3. DATA ENGINE (Chargement de toutes les données) ---
@st.cache_data(ttl=3600)
def load_full_data():
    """Charge toutes les données sans filtre."""
    if not os.path.exists(FILE_PATH):
        # Données de démonstration
        data = {
            'Reseau': ['Métro', 'RER', 'Métro', 'RER', 'Tramway', 'Métro', 'RER', 'Métro', 'Tramway', 'Métro'],
            'Station': ['Châtelet', 'Gare du Nord', 'Gare de Lyon', 'La Défense', 'Porte de Versailles', 'Saint-Lazare', 'Auber', 'Montparnasse', 'T3a', 'Nation'],
            'Trafic': [35000000, 32000000, 28000000, 25000000, 10000000, 24000000, 20000000, 18000000, 15000000, 12000000],
            'Ville': ['Paris 1er', 'Paris 10e', 'Paris 12e', 'Puteaux', 'Paris 15e', 'Paris 8e', 'Paris 9e', 'Paris 14e', 'Paris 15e', 'Paris 11e']
        }
        df = pd.DataFrame(data)
        df['Rang'] = df['Trafic'].rank(ascending=False)
        st.warning("Utilisation de données de démonstration : Le chemin de fichier est introuvable.")
        return df

    # Le reste du code de chargement et nettoyage est inchangé
    try:
        df = pd.read_csv(FILE_PATH, sep=';', encoding='utf-8')
    except Exception as e:
        st.error(f"Erreur de lecture du fichier CSV : {e}")
        return pd.DataFrame()

    df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]

    def get_col(keys):
        for c in df.columns:
            if any(k in c for k in keys): return c
        return None

    mapping = {
        'Reseau': get_col(['reseau', 'réseau']),
        'Station': get_col(['station', 'nom']),
        'Trafic': get_col(['trafic', 'validations']),
        'Ville': get_col(['ville', 'commune']),
        'Arr': get_col(['arrondissement'])
    }
    
    final_cols = {v: k for k, v in mapping.items() if v}
    df = df.rename(columns=final_cols)

    if 'Trafic' in df.columns:
        df['Trafic'] = df['Trafic'].astype(str).str.replace(r'\s+', '', regex=True)
        df['Trafic'] = pd.to_numeric(df['Trafic'], errors='coerce').fillna(0).astype(int)

    if 'Ville' in df.columns:
        df['Ville'] = df['Ville'].fillna("Inconnue").str.title()
        if 'Arr' in df.columns:
            mask_paris = df['Ville'].str.contains('Paris', case=False)
            df.loc[mask_paris, 'Ville'] = df.loc[mask_paris, 'Ville'] + " " + df.loc[mask_paris, 'Arr'].astype(str)

    if 'Reseau' in df.columns:
        df['Reseau'] = df['Reseau'].fillna("Autre").str.replace('Metro', 'Métro')

    df['Rang'] = df['Trafic'].rank(ascending=False)
    
    return df

# --- Fonction de récupération des données filtrées pour les PAGES ---
# C'est la fonction qui est appelée par les pages pour obtenir le DF filtré.
@st.cache_data(ttl=3600)
def load_data():
    """Retourne la DataFrame filtrée stockée dans st.session_state."""
    if 'df_filtered' in st.session_state:
        return st.session_state['df_filtered']
    
    # Fallback pour le premier chargement ou si l'état est perdu
    return load_full_data()


# --- 4. VISUALIZATION FACTORY (Fonctions des graphiques pour les imports des pages) ---

def chart_sunburst(df):
    fig = px.sunburst(
        df.head(150), path=['Reseau', 'Ville', 'Station'], values='Trafic',
        color='Reseau', color_discrete_map=PLOTLY_COLOR_MAP, 
        title="🌌 Hiérarchie du Trafic (Top 150)", template=PLOT_THEME
    )
    return fig

def chart_pareto(df):
    sorted_df = df.sort_values('Trafic', ascending=False)
    sorted_df['Cumul_Trafic'] = sorted_df['Trafic'].cumsum()
    sorted_df['Cumul_Percent'] = sorted_df['Cumul_Trafic'] / sorted_df['Trafic'].sum() * 100
    sorted_df['Station_Percent'] = sorted_df.reset_index(drop=True).index.to_series().apply(lambda x: (x + 1) / len(sorted_df) * 100)
    
    fig = px.area(
        sorted_df, x='Station_Percent', y='Cumul_Percent',
        title="📉 Courbe de Concentration (Pareto)",
        labels={'Station_Percent': '% des Stations', 'Cumul_Percent': '% du Trafic Cumulé'},
        template=PLOT_THEME
    )
    fig.update_traces(line_color=COLOR_PARETO_LINE, fillcolor=COLOR_PARETO_FILL)
    fig.add_hline(y=80, line_dash="dot", line_color=COLOR_PARETO_80_20, annotation_text="80% Trafic")
    return fig

def chart_scatter_zipf(df):
    fig = px.scatter(
        df, x='Rang', y='Trafic', color='Reseau',
        log_x=True, log_y=True, hover_name='Station',
        color_discrete_map=PLOTLY_COLOR_MAP, 
        title="⚡ Distribution Zipf (Échelle Log-Log)", template=PLOT_THEME
    )
    return fig

def chart_heatmap(df):
    top_cities = df.groupby('Ville')['Trafic'].sum().nlargest(15).index
    df_heat = df[df['Ville'].isin(top_cities)]
    
    pivot = df_heat.pivot_table(index='Ville', columns='Reseau', values='Trafic', aggfunc='sum', fill_value=0)
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Réseau", y="Ville", color="Trafic"),
        color_continuous_scale=[(0, "white"), (0.5, COLOR_PARETO_LINE), (1, COLOR_HEATMAP_END)],
        title="🔥 Heatmap: Intensité par Ville/Réseau", template=PLOT_THEME
    )
    return fig

def chart_violin(df):
    fig = px.violin(
        df, y="Trafic", x="Reseau", color="Reseau",
        box=True, points="all", hover_name="Station",
        color_discrete_map=PLOTLY_COLOR_MAP, log_y=True,
        title="🎻 Densité & Dispersion du Trafic", template=PLOT_THEME
    )
    return fig

def chart_bar_race(df):
    top = df.nlargest(15, 'Trafic')
    fig = px.bar(
        top, x='Trafic', y='Station', orientation='h',
        color='Reseau', color_discrete_map=PLOTLY_COLOR_MAP, 
        text_auto='.2s',
        title="🏆 Le Club des Géants (Top 15)", template=PLOT_THEME
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig


# --- 5. MAIN APP ENGINE (Page d'Accueil & Gestion des Filtres) ---
def main():
    st.title("🚇 RATP DATA STUDIO")
    
    df = load_full_data()
    
    if df.empty:
        st.error("⚠️ Impossible de charger les données ou d'utiliser les données de démonstration.")
        return

    # --- SIDEBAR & FILTERS ---
    st.sidebar.header("🎛️ CENTRE DE CONTRÔLE")
    
    all_reseaux = df['Reseau'].unique()
    
    # Initialisation de l'état de session si non existant
    if 'selected_reseaux' not in st.session_state:
        st.session_state['selected_reseaux'] = all_reseaux
    if 'search_station' not in st.session_state:
        st.session_state['search_station'] = ""
    
    # Application des filtres et mise à jour de l'état
    sel_res = st.sidebar.multiselect(
        "Réseaux", all_reseaux, 
        default=st.session_state['selected_reseaux'],
        key='ms_reseaux'
    )
    st.session_state['selected_reseaux'] = sel_res
    
    search_station = st.sidebar.text_input(
        "🔍 Rechercher Station", 
        value=st.session_state['search_station'],
        key='ti_station'
    )
    st.session_state['search_station'] = search_station
    
    # Data Filtering pour les KPI et le stockage dans session_state
    df_viz = df[df['Reseau'].isin(st.session_state['selected_reseaux'])]
    if st.session_state['search_station'] and 'Station' in df_viz.columns:
        df_viz = df_viz[df_viz['Station'].str.contains(st.session_state['search_station'], case=False)]

    # Stockage du DataFrame filtré pour que les pages y aient accès via load_data()
    st.session_state['df_filtered'] = df_viz
    
    # --- KPI BOARD ---
    total = df_viz['Trafic'].sum() if not df_viz.empty else 0
    max_station_loc = df_viz['Trafic'].idxmax() if not df_viz.empty and not df_viz['Trafic'].empty else None
    max_station = df_viz.loc[max_station_loc] if max_station_loc is not None else None
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TRAFIC GLOBAL", f"{total:,.0f}".replace(",", " "), "Voyageurs")
    k2.metric("STATIONS ACTIVES", len(df_viz), "Points d'arrêt")
    
    if max_station is not None and 'Station' in max_station:
        k3.metric("TOP STATION", max_station['Station'], f"{max_station['Trafic']/1e6:.1f}M")
        share = (max_station['Trafic'] / total * 100) if total > 0 else 0
        k4.metric("DOMINANCE TOP 1", f"{share:.2f}%", "Part de marché")
    else:
        k3.metric("TOP STATION", "N/A", "0M")
        k4.metric("DOMINANCE TOP 1", "0.00%", "Part de marché")

    st.markdown("---")
    
    st.info("🎯 **Page d'Accueil :** Le tableau de bord ci-dessus montre les indicateurs clés de performance (KPI) basés sur vos filtres. Veuillez utiliser le menu de navigation à gauche pour accéder aux différentes pages d'analyse (Graphiques).")


if __name__ == "__main__":
    main()