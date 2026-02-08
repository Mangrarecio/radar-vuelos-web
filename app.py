import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CONFIGURACIÓN DE ACCESO ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

@st.cache_data(ttl=120)
def obtener_datos_vuelo():
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lamax': 44.5, 'lomin': -10.0, 'lomax': 4.5}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        # Intento de conexión con credenciales
        r = requests.get(url, params=params, auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), timeout=20, headers=headers)
        
        # Fallback a modo anónimo si las credenciales fallan
        if r.status_code == 401:
            r = requests.get(url, params=params, timeout=15, headers=headers)
            status = "Conexión Pública"
        elif r.status_code == 200:
            status = f"Usuario: {USER_OPENSKY}"
        else:
            status = f"Estado API: {r.status_code}"

        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, status
        return None, status
    except:
        return None, "Error de red"

# --- INTERFAZ ---
st.title("🛰️ Radar de Vuelos Satelital")

df, status_msg = obtener_datos_vuelo()

st.sidebar.header("📡 Estado del Sistema")
st.sidebar.info(status_msg)

# Generación del Mapa Satelital
m = folium.Map(
    location=[40.41, -3.70], 
    zoom_start=6, 
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite'
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
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aeronaves.")
else:
    st.warning(f"Sincronizando: {status_msg}")

st_folium(m, width="100%", height=600)