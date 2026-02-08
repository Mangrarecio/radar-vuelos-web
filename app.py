import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CONFIGURACIÓN ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

# Caché de 2 minutos para NO saturar la API (Respetando las limitaciones)
@st.cache_data(ttl=120) 
def obtener_vuelos_eficiente():
    # Sector: España
    url = "https://opensky-network.org/api/states/all?lamin=35.0&lomin=-10.0&lamax=44.0&lomax=4.0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Petición oficial con tu cuenta
        r = requests.get(url, auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), timeout=15, headers=headers)
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "Datos Actualizados"
        
        if r.status_code == 429:
            return None, "API en espera (Límite de velocidad)"
        return None, f"Estado: {r.status_code}"
    except:
        return None, "Error de conexión"

# --- INTERFAZ ---
st.title("🛰️ Radar de Vuelos - Sector España")

df, status_msg = obtener_vuelos_eficiente()

# Sidebar informativa
st.sidebar.header("📡 Info de Conexión")
st.sidebar.info(f"Usuario: {USER_OPENSKY}")
st.sidebar.write(f"Estado API: {status_msg}")

# --- MAPA SATELITAL ---
m = folium.Map(
    location=[40.41, -3.70], 
    zoom_start=6, 
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satélite'
)

if df is not None:
    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']} | Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 20px; text-shadow: 1px 1px 2px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aviones detectados.")
else:
    st.warning("Petición en cola. Los aviones aparecerán automáticamente en breve.")

st_folium(m, width="100%", height=600, key="mapa_final")