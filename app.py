import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- VOLVEMOS A LAS CREDENCIALES DE USUARIO (Más estables) ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital Pro", layout="wide")

@st.cache_data(ttl=120)
def obtener_vuelos_final_v26():
    url = "https://opensky-network.org/api/states/all"
    # Ajustamos el área a la Península e Islas
    params = {'lamin': 34.0, 'lamax': 44.5, 'lomin': -10.0, 'lomax': 4.5}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    }
    
    try:
        # Usamos Autenticación Básica con usuario y contraseña
        r = requests.get(
            url, 
            params=params, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY),
            headers=headers,
            timeout=20
        )
        
        # Si da 401 con usuario, intentamos entrar como ANÓNIMO (Modo Público)
        if r.status_code == 401:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            status = "📡 Conectado (Modo Público)"
        elif r.status_code == 200:
            status = f"🟢 Conectado como {USER_OPENSKY}"
        else:
            status = f"⚠️ Estado: {r.status_code}"

        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, status
        
        if r.status_code == 429:
            return None, "🔴 API Saturada (429): Espera 3 min"
        return None, status
            
    except Exception as e:
        return None, "📡 Buscando señal del servidor..."

# --- INTERFAZ ---
st.title("🌍 Radar Satelital de España")

df, status_msg = obtener_vuelos_final_v26()

st.sidebar.header("📊 Sistema")
st.sidebar.info(f"Estado: {status_msg}")

# Mapa Satelital de Google
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
                popup=f"Vuelo: {v['callsign']}",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar Activo: {len(df)} aviones.")
else:
    st.warning(status_msg)

st_folium(m, width="100%", height=600, key="radar_final_v26")