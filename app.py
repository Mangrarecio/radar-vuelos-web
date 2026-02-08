import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CREDENCIALES ---
# Asegúrate de que el ID no tenga espacios
CLIENT_ID = "mangrarecio-api-client" 
CLIENT_SECRET = "c6yQEHTTqDM2Udi41RI98t4UUur49anO"

st.set_page_config(page_title="Radar Satelital Profesional", layout="wide")

@st.cache_data(ttl=180)
def obtener_vuelos_definitivo():
    # Simplificamos la URL al máximo
    url = "https://opensky-network.org/api/states/all"
    # España: Coordenadas simplificadas
    params = {
        'lamin': 34.0, 'lamax': 45.0,
        'lomin': -10.0, 'lomax': 5.0
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    }
    
    try:
        # Intentamos conexión directa
        # Usamos timeout largo de 20 segundos por si el servidor está lento
        r = requests.get(
            url, 
            params=params, 
            auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
            headers=headers,
            timeout=20 
        )
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Radar Online"
            return None, "☁️ Sin tráfico detectado"
        
        elif r.status_code == 429:
            return None, "🔴 Saturación: Esperando desbloqueo (5 min)"
        elif r.status_code == 401:
            return None, "❌ Error 401: Llaves no activas"
        else:
            return None, f"⚠️ Error {r.status_code}"
            
    except Exception as e:
        # Si hay error de red, intentamos una vez más sin autenticación (Modo Público)
        try:
            r_anon = requests.get(url, params=params, headers=headers, timeout=10)
            if r_anon.status_code == 200:
                return obtener_vuelos_definitivo.__wrapped__()
        except:
            pass
        return None, "📡 Buscando señal del servidor..."

# --- INTERFAZ ---
st.title("🌍 Radar Satelital de España")

df, status_msg = obtener_vuelos_definitivo()

st.sidebar.header("📊 Sistema")
st.sidebar.info(f"Estado: {status_msg}")

# Mapa Satelital de Google (Este nunca falla)
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

st_folium(m, width="100%", height=600, key="radar_v25")