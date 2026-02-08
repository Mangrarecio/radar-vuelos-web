import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth
import time

# --- CREDENCIALES ---
CLIENT_ID = "mangrarecio-api-client" 
CLIENT_SECRET = "c6yQEHTTqDM2Udi41RI98t4UUur49anO"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

# Caché de 3 minutos para que la API nos quite el bloqueo 429
@st.cache_data(ttl=180)
def obtener_vuelos_paciencia():
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lamax': 44.5, 'lomin': -10.0, 'lomax': 4.5}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RadarPro/1.0'}
    
    try:
        # Intento con tus credenciales OAuth
        r = requests.get(url, params=params, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET), timeout=15, headers=headers)
        
        # Si las llaves fallan, intentar anónimo
        if r.status_code == 401:
            r = requests.get(url, params=params, timeout=15, headers=headers)

        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Radar Conectado"
        
        if r.status_code == 429:
            return None, "🔴 API Saturada: Esperando turno (3-5 min)"
        return None, f"⚠️ Estado API: {r.status_code}"
    except:
        return None, "❌ Error de conexión"

# --- INTERFAZ ---
st.title("🌍 Radar de Vuelos Satelital Pro")

df, status_msg = obtener_vuelos_paciencia()

# Sidebar
st.sidebar.header("📡 Diagnóstico")
st.sidebar.markdown(f"**Estado:** {status_msg}")
if "🔴" in status_msg:
    st.sidebar.warning("Por favor, no refresques la página. El sistema se conectará solo en unos minutos.")

# --- MAPA SATELITAL ---
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
            # Colores por altitud: Rojo (bajo), Amarillo (medio), Verde (crucero)
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']} | Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aeronaves detectadas.")
else:
    st.info("🛰️ Mapa base listo. Sincronizando datos de vuelo...")

st_folium(m, width="100%", height=600, key="mapa_final_v20")