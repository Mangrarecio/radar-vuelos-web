import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from requests.auth import HTTPBasicAuth

# --- CREDENCIALES ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

st.set_page_config(page_title="Radar Satelital Pro", layout="wide")

# Caché agresiva para evitar el baneo (429)
@st.cache_data(ttl=180) # Esperamos 3 minutos entre actualizaciones
def obtener_datos_oficiales():
    # Coordenadas exactas para cubrir España y Portugal
    params = {
        'lamin': 34.0,
        'lomin': -10.0,
        'lamax': 44.5,
        'lomax': 4.5
    }
    
    url = "https://opensky-network.org/api/states/all"
    
    try:
        # Según la documentación, enviar un User-Agent específico ayuda
        headers = {'User-Agent': 'OpenSkyPythonAPI/1.4.0'}
        
        r = requests.get(
            url, 
            params=params, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY),
            headers=headers,
            timeout=20
        )
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "OK"
            return None, "Área sin tráfico ahora"
        elif r.status_code == 429:
            return None, "API Saturada (Espera 3 min)"
        elif r.status_code == 401:
            return None, "Credenciales no aceptadas"
        else:
            return None, f"Error {r.status_code}"
    except:
        return None, "Fallo de conexión"

# --- INTERFAZ ---
st.title("🛰️ Radar Satelital (Doc. 1.4.0)")

df, msg = obtener_datos_oficiales()

# Panel de control
st.sidebar.header("📡 Estado")
st.sidebar.write(f"**Usuario:** {USER_OPENSKY}")
st.sidebar.info(f"Respuesta: {msg}")

# Mapa Satelital de Google (El que ya viste que funciona)
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
            # Colores: Rojo (bajo), Amarillo (medio), Verde (alto)
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']}<br>Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar en línea: {len(df)} aviones detectados.")
else:
    st.warning(f"⚠️ {msg}. El terreno satelital se cargará primero.")

st_folium(m, width="100%", height=600, key="mapa_final")