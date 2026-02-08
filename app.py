import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- CREDENCIALES APIFY ---
# Usamos el token que me pasaste como password del proxy
APIFY_TOKEN = "apify_api_fadESORCWQXTB7EaZDOdO4fGDKC8yx0lSmqz"

st.set_page_config(page_title="Radar Satelital Ultra-Pro", layout="wide")

@st.cache_data(ttl=60)
def obtener_vuelos_apify_v2():
    url_opensky = "https://opensky-network.org/api/states/all"
    params = {'lamin': 34.0, 'lomin': -10.0, 'lamax': 44.5, 'lomax': 4.5}
    
    # ESTRUCTURA CORRECTA PARA APIFY PROXY
    # Formato: http://groups-RESIDENTIAL:TOKEN@proxy.apify.com:8000
    proxy_url = f"http://groups-RESIDENTIAL:{APIFY_TOKEN}@proxy.apify.com:8000"
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        # Hacemos la petición a través del proxy residencial
        r = requests.get(url_opensky, params=params, proxies=proxies, timeout=30)
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Túnel Apify Establecido"
        
        return None, f"Error del Servidor: {r.status_code}"
    except Exception as e:
        return None, f"Reintentando conexión... (Causa: {str(e)[:50]})"

# --- INTERFAZ ---
st.title("🛰️ Radar Satelital (Vía Proxy Residencial)")

df, status_msg = obtener_vuelos_apify_v2()

st.sidebar.header("📡 Estado del Túnel")
st.sidebar.info(status_msg)

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
                popup=f"Vuelo: {v['callsign']}<br>Altitud: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Radar Activo: {len(df)} aviones detectados.")
else:
    st.warning(f"Esperando datos del túnel... {status_msg}")

st_folium(m, width="100%", height=600, key="mapa_v22")