import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests

# --- CREDENCIALES ---
# Usamos el API TOKEN de Apify para autenticarnos en su plataforma
APIFY_TOKEN = "apify_api_fadESORCWQXTB7EaZDOdO4fGDKC8yx0lSmqz"

st.set_page_config(page_title="Radar Satelital Ultra-Pro", layout="wide")

@st.cache_data(ttl=60)
def obtener_vuelos_via_apify():
    # URL de OpenSky con los filtros de España
    target_url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    
    # Usamos el "API de transferencia" de Apify que es más estable que el proxy directo
    # Esto envía la petición desde los servidores de Apify y nos devuelve el resultado
    apify_request_url = f"https://api.apify.com/v2/browser-info?token={APIFY_TOKEN}" # Test de conexión
    
    # Intentamos una petición HTTP simple a través del proxy de Apify usando su formato de Gateway
    proxy_url = f"http://groups-RESIDENTIAL:{APIFY_TOKEN}@proxy.apify.com:8000"
    
    try:
        # Forzamos la sesión para que no se pierda la autenticación
        session = requests.Session()
        session.proxies = {"http": proxy_url, "https": proxy_url}
        
        # Hacemos la petición a OpenSky
        r = session.get(target_url, timeout=30)
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "🟢 Conectado vía Apify Gateway"
        
        return None, f"Estado: {r.status_code} (Revisar plan de Apify)"
    except Exception as e:
        # Si el proxy residencial falla, intentamos el modo directo (último recurso)
        try:
            r_direct = requests.get(target_url, timeout=10)
            if r_direct.status_code == 200:
                return obtener_vuelos_via_apify.__wrapped__() # Fallback
        except:
            pass
        return None, "🔴 Error de Túnel: Verifica que el Proxy Residencial esté activo en Apify"

# --- INTERFAZ ---
st.title("🛰️ Radar Satelital (Conexión Blindada)")

df, status_msg = obtener_vuelos_via_apify()

st.sidebar.header("📊 Centro de Control")
st.sidebar.info(f"Estado: {status_msg}")

# Mapa de Google Satélite (Siempre funcional)
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
    st.success(f"Radar en línea: {len(df)} aviones.")
else:
    st.warning(status_msg)

st_folium(m, width="100%", height=600, key="mapa_v23")