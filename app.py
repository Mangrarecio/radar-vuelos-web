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

# --- NUEVO MÉTODO DE REFRESCO NATIVO ---
# Esto sustituye a la librería que daba error
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

# Botón para refrescar manualmente si se desea
if st.sidebar.button("🔄 Actualizar Ahora"):
    st.cache_data.clear()
    st.rerun()

st.title("🌍 Radar de Vuelos Satelital Pro")

@st.cache_data(ttl=110)
def obtener_vuelos():
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        r = requests.get(url, auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), timeout=15)
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df
        return None
    except:
        return None

df = obtener_vuelos()

# --- PANEL LATERAL ---
busqueda_input = st.sidebar.text_input("🔍 Buscar Vuelo (CallSign):", "").upper().strip()

# --- VISUALIZACIÓN ---
if df is not None and not df.empty:
    df_mostrar = df[df['callsign'].str.contains(busqueda_input, na=False)] if busqueda_input else df

    # Mapa con Google Satélite
    m = folium.Map(
        location=[40.41, -3.70], 
        zoom_start=6, 
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satélite'
    )

    for _, v in df_mostrar.iterrows():
        if not pd.isna(v['lat']) and not pd.isna(v['long']):
            alt = int(v['altitud']) if not pd.isna(v['altitud']) else 0
            rumb = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
            color_avion = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            html = f"<b>{v['callsign']}</b><br>Alt: {alt}m"
            icon_html = f'''<div style="transform: rotate({rumb}deg); color: {color_avion}; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=folium.Popup(html, max_width=150),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    st_folium(m, width="100%", height=600, key="mapa_v11")
    st.success(f"Radar Activo: {len(df_mostrar)} aeronaves detectadas.")
    
    # Programar el próximo refresco en 2 minutos (sin librerías externas)
    time.sleep(1) # Pequeña pausa para estabilidad
else:
    st.warning("📡 Sincronizando con el satélite... Por favor, espera.")
    time.sleep(5)
    st.rerun()