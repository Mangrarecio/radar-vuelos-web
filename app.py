import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth
import time

# --- CONFIGURACIÓN ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital PRO", layout="wide")

# Caché de larga duración (5 min) para dejar respirar a la API si hay error
@st.cache_data(ttl=300) 
def obtener_vuelos_enfriamiento():
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lomin': -10.0, 'lamax': 44.5, 'lomax': 4.5}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RadarPro/1.4.0'}
    
    try:
        # Intentamos con tus credenciales
        r = requests.get(url, params=params, auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), timeout=15, headers=headers)
        
        # Si las credenciales fallan, intentamos anónimo
        if r.status_code == 401:
            r = requests.get(url, params=params, headers=headers, timeout=15)

        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Radar Operativo"
        
        if r.status_code == 429:
            return None, "🔴 API Saturada: Enfriamiento activo (5 min)"
        return None, f"⚠️ Estado API: {r.status_code}"
    except:
        return None, "❌ Error de conexión"

# --- INTERFAZ ---
st.title("🌍 Radar de Vuelos Satelital Pro")

df, estado_msg = obtener_vuelos_enfriamiento()

# Sidebar
st.sidebar.header("📡 Diagnóstico")
st.sidebar.markdown(f"**Estado:** {estado_msg}")
if "🔴" in estado_msg:
    st.sidebar.warning("No refresques la página. El sistema está esperando a que la API se libere automáticamente.")

# --- MAPA ---
m = folium.Map(location=[40.41, -3.70], zoom_start=6, 
               tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
               attr='Google Satellite')

if df is not None:
    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']}",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar Activo: {len(df)} aeronaves.")
else:
    st.info("🛰️ Mapa base cargado. Esperando datos del satélite...")

st_folium(m, width="100%", height=600, key="mapa_final_v17")