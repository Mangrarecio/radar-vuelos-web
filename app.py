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

st.set_page_config(page_title="Radar Satelital Premium", layout="wide")

# Usamos caché de larga duración para el error 429
@st.cache_data(ttl=120) # Si falla, no reintentes en 2 minutos
def obtener_vuelos_limpio():
    url = "https://opensky-network.org/api/states/all?lamin=35.0&lomin=-10.0&lamax=44.0&lomax=4.0"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Intentamos con tus credenciales
        r = requests.get(url, auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), timeout=10, headers=headers)
        
        # Si da 429 o 401, intentamos anónimo tras un mini respiro
        if r.status_code in [401, 429]:
            time.sleep(1)
            r = requests.get(url, timeout=10, headers=headers)
            
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "Conexión Exitosa"
        
        if r.status_code == 429:
            return None, "API Saturada (Espera 2 min)"
        return None, f"Estado: {r.status_code}"
    except:
        return None, "Error de red"

# --- INTERFAZ ---
st.title("🌍 Radar de Vuelos Satelital Pro")

df, status_msg = obtener_vuelos_limpio()

# Panel lateral
st.sidebar.header("📊 Info del Radar")
st.sidebar.warning(f"Aviso: {status_msg}")
busqueda = st.sidebar.text_input("🔍 Filtrar Vuelo:", "").upper()

# Botón de pánico (solo usar si llevas mucho esperando)
if st.sidebar.button("🔄 Forzar Reintento"):
    st.cache_data.clear()
    st.rerun()

# --- MAPA SATELITAL ---
m = folium.Map(
    location=[40.41, -3.70], 
    zoom_start=6, 
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satélite'
)

if df is not None and not df.empty:
    df_filtrado = df[df['callsign'].str.contains(busqueda, na=False)] if busqueda else df
    for _, v in df_filtrado.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']} | Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 20px; text-shadow: 1px 1px 2px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Visualizando {len(df_filtrado)} aviones.")
else:
    st.info("🛰️ El mapa satelital está listo. Esperando que la API de OpenSky libere los datos...")

st_folium(m, width="100%", height=600, key="mapa_v14")