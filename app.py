import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURACIÓN ESTADO ---
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Satelital Pro", layout="wide")
st_autorefresh(interval=120000, key="datarefresh")

st.title("🌍 Radar de Vuelos Satelital")

# --- PANEL LATERAL CON SOLUCIÓN AL BUSCADOR ---
st.sidebar.header("🔍 Seguimiento de Vuelo")

# Input de búsqueda
busqueda_input = st.sidebar.text_input("Introduce CallSign (ej: IBE2622):", key="search_box").upper().strip()

# Botón para limpiar rápido
if st.sidebar.button("Mostrar todos los vuelos"):
    st.session_state.search_box = ""
    st.rerun()

@st.cache_data(ttl=110)
def obtener_vuelos():
    # Coordenadas de España + un poco de margen
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        r = requests.get(url, timeout=10)
        datos = r.json()
        columnas = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
        df = pd.DataFrame([fila[:12] for fila in datos['states']], columns=columnas)
        df['callsign'] = df['callsign'].str.strip()
        return df
    except:
        return None

df = obtener_vuelos()

if df is not None:
    # Lógica de filtrado automático
    df_mostrar = df[df['callsign'].str.contains(busqueda_input, na=False)] if busqueda_input else df

    # --- MAPA VISTA SATÉLITE ---
    # Usamos ESRI World Imagery para una vista realista de satélite
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )

    for _, v in df_mostrar.iterrows():
        if not pd.isna(v['lat']) and not pd.isna(v['long']):
            call = v['callsign'] if v['callsign'] else "S/N"
            alt = int(v['altitud']) if v['altitud'] else 0
            vel = int(v['velocidad'] * 3.6) if v['velocidad'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            
            # Datos interesantes "Deducidos"
            # (El origen/destino real requiere una cuenta de pago en OpenSky, 
            # pero aquí mostramos la info técnica disponible)
            html_popup = f"""
            <div style="width: 200px; font-family: Arial;">
                <b style="color: #e67e22; font-size: 14px;">✈ Vuelo: {call}</b><br>
                <hr>
                <b>Transpondedor:</b> {v['icao24'].upper()}<br>
                <b>Origen (País):</b> {v['pais']}<br>
                <b>Altitud:</b> {alt} m ({int(alt*3.28)} ft)<br>
                <b>Velocidad:</b> {vel} km/h<br>
                <b>Rumbo:</b> {rumb}º<br>
                <p style="font-size: 10px; color: gray;">Información vía ADS-B RealTime</p>
            </div>
            """
            
            # Icono que rota según el rumbo
            icon_html = f'''<div style="transform: rotate({rumb}deg); color: #FFF; text-shadow: 0 0 3px #000; font-size: 20px;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=folium.Popup(html_popup, max_width=250),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # Renderizado
    output = st_folium(m, width="100%", height=600, key="mapa_sat", returned_objects=["zoom", "center"])

    # Guardar posición
    if output:
        if output.get('center'): st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
        if output.get('zoom'): st.session_state['map_zoom'] = output['zoom']

    st.info(f"Mostrando {len(df_mostrar)} aviones sobre el terreno.")
else:
    st.error("Esperando datos del satélite...")