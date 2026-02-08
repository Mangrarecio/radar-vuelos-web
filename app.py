import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. MEMORIA DE LA PÁGINA
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Pro - Blindado", layout="wide")

st_autorefresh(interval=30000, key="datarefresh")

st.title("🛰️ Centro de Control Aéreo (Versión Estable)")

def obtener_vuelos():
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
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles="CartoDB dark_matter"
    )

    for _, v in df.iterrows():
        # --- LIMPIEZA DE DATOS NIVEL EXPERTO ---
        # Usamos pd.isna() para detectar CUALQUIER tipo de valor vacío
        lat, lon = v['lat'], v['long']
        
        if not pd.isna(lat) and not pd.isna(lon):
            # Creamos variables seguras
            callsign = v['callsign'] if not pd.isna(v['callsign']) else "???"
            
            # Si el valor no es un número válido, ponemos 0
            try:
                altitud = int(v['altitud']) if not pd.isna(v['altitud']) else 0
                velocidad = int(v['velocidad'] * 3.6) if not pd.isna(v['velocidad']) else 0
                rumbo = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
            except:
                altitud, velocidad, rumbo = 0, 0, 0
                
            pais = v['pais'] if not pd.isna(v['pais']) else "Internacional"

            # Ventana emergente
            html_popup = f"""
            <div style="font-family: sans-serif; min-width: 180px;">
                <h4 style="color: #007bff; margin: 0;">{callsign}</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 2px 0;"><b>País:</b> {pais}</p>
                <p style="margin: 2px 0;"><b>Alt:</b> {altitud} m</p>
                <p style="margin: 2px 0;"><b>Vel:</b> {velocidad} km/h</p>
            </div>
            """
            
            icon_html = f'''<div style="transform: rotate({rumbo}deg); color: #00FF00; font-size: 18px;">✈</div>'''
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html_popup, max_width=300),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # Mostrar mapa y capturar interacción
    output = st_folium(m, width="100%", height=600, key="mapa_v5")

    # Guardar posición para que no se resetee el zoom
    if output and output.get('center'):
        st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
    if output and output.get('zoom'):
        st.session_state['map_zoom'] = output['zoom']

else:
    st.info("Esperando datos de la API de OpenSky...")