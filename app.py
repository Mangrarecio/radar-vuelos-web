import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth
import time

# --- CREDENCIALES FIJAS ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital PRO", layout="wide")

# Forzamos un estilo visual profesional desde el inicio
st.title("🌍 Radar de Vuelos Satelital Pro")

# --- SISTEMA DE DESCARGA PROFESIONAL ---
@st.cache_data(ttl=150) # Esperamos 2.5 minutos entre peticiones para evitar bloqueos
def descargar_datos():
    # Coordenadas rectificadas de la Península e Islas
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    
    # Cabecera simulando un navegador real para evitar bloqueos por 'User-Agent'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        r = requests.get(
            url, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), 
            headers=headers, 
            timeout=20
        )
        
        if r.status_code == 200:
            data = r.json()
            if data and 'states' in data and data['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in data['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "Conectado"
            return None, "Sin vuelos en el área"
        
        elif r.status_code == 429:
            return None, "API Saturada (Límite 429)"
        elif r.status_code == 401:
            return None, "Error 401: Credenciales no activas"
        else:
            return None, f"Estado API: {r.status_code}"
            
    except Exception as e:
        return None, f"Fallo de Red: {str(e)}"

# --- EJECUCIÓN ---
df, estado = descargar_datos()

# Sidebar
st.sidebar.header("📊 Centro de Control")
st.sidebar.markdown(f"**Usuario:** `{USER_OPENSKY}`")
st.sidebar.markdown(f"**Estado:** {estado}")

if st.sidebar.button("🔄 Forzar Reintento Manual"):
    st.cache_data.clear()
    st.rerun()

# --- MAPA (SIEMPRE VISIBLE) ---
# Centrado en Madrid con el zoom que pediste
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
            # Color por altitud
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']}<br>Altitud: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aeronaves.")
else:
    st.warning(f"⚠️ {estado}. El mapa se actualizará cuando la API esté libre.")

# Mostramos el mapa
st_folium(m, width="100%", height=600, key="mapa_final_estable")