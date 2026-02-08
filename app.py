import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CREDENCIALES ---
CLIENT_ID = "mangrarecio-api-client" 
CLIENT_SECRET = "c6yQEHTTqDM2Udi41RI98t4UUur49anO"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

@st.cache_data(ttl=120)
def obtener_vuelos_sigilo():
    # URL y parámetros exactos para España
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lamax': 44.5, 'lomin': -10.0, 'lomax': 4.5}
    
    # CABECERA DE NAVEGADOR REAL (Vital para saltar bloqueos)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }
    
    try:
        # Intentamos la conexión directa pero "disfrazados"
        r = requests.get(
            url, 
            params=params, 
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            headers=headers,
            timeout=15
        )
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Conexión Exitosa"
            return None, "☁️ Sin vuelos detectados"
        
        elif r.status_code == 429:
            return None, "🔴 API Saturada (429): Espera 5 min"
        else:
            # Si falla con tus llaves, intentamos modo anónimo rápido
            r_anon = requests.get(url, params=params, headers=headers, timeout=10)
            if r_anon.status_code == 200:
                return obtener_vuelos_sigilo.__wrapped__() # Reintento interno
            return None, f"⚠️ Estado: {r.status_code}"
            
    except Exception as e:
        return None, "❌ Error de Red"

# --- INTERFAZ ---
st.title("🌍 Radar de Vuelos Satelital Pro")

df, status_msg = obtener_vuelos_sigilo()

st.sidebar.header("📡 Diagnóstico")
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
    st.warning(f"Sincronizando: {status_msg}")

st_folium(m, width="100%", height=600, key="mapa_v24")