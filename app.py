import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CREDENCIALES NUEVAS ---
# Nota: He limpiado el espacio en blanco del ID que venía en tu mensaje
CLIENT_ID = "mangrarecio-api-client" 
CLIENT_SECRET = "c6yQEHTTqDM2Udi41RI98t4UUur49anO"

st.set_page_config(page_title="Radar Satelital Ultra-Pro", layout="wide")

@st.cache_data(ttl=120)
def obtener_vuelos_definitivo():
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lamax': 44.5, 'lomin': -10.0, 'lomax': 4.5}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # INTENTO 1: Con API Client
        r = requests.get(url, params=params, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET), timeout=15, headers=headers)
        
        # INTENTO 2: Si falla el 401, intentar Anónimo
        if r.status_code == 401:
            r = requests.get(url, params=params, timeout=15, headers=headers)
            status = "Conectado (Modo Público)"
        else:
            status = "Conectado (Modo API Client)"

        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, status
        
        if r.status_code == 429:
            return None, "API Ocupada (429) - Espera 2 min"
        return None, f"Error {r.status_code}"
    except:
        return None, "Error de red"

# --- INTERFAZ ---
st.title("🛰️ Radar Satelital Profesional")

df, status_msg = obtener_vuelos_definitivo()

st.sidebar.header("📊 Sistema")
st.sidebar.info(f"Estado: {status_msg}")

# Mapa Satelital de Google (Carga siempre)
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
                popup=f"Vuelo: {v['callsign']}<br>Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar Activo: {len(df)} aeronaves.")
else:
    st.warning(f"Sincronizando: {status_msg}")

st_folium(m, width="100%", height=600, key="mapa_v19")