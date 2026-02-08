import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. MEMORIA DE LA PÁGINA (Session State)
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Pro Interactiva", layout="wide")

# Actualización automática cada 30 segundos
st_autorefresh(interval=30000, key="datarefresh")

st.title("🛰️ Centro de Control Aéreo Interactivo")

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
        # --- LIMPIEZA DE DATOS (Seguridad ante Nones) ---
        # Si el dato existe, lo convertimos a int; si no, ponemos 0 o "N/A"
        lat, lon = v['lat'], v['long']
        
        if lat and lon:
            callsign = v['callsign'] if v['callsign'] else "DESCONOCIDO"
            altitud = int(v['altitud']) if v['altitud'] is not None else 0
            velocidad = int(v['velocidad'] * 3.6) if v['velocidad'] is not None else 0
            rumbo = int(v['rumbo']) if v['rumbo'] is not None else 0
            v_vertical = v['v_vertical'] if v['v_vertical'] is not None else 0
            pais = v['pais'] if v['pais'] else "No disponible"

            # 2. VENTANA EMERGENTE PROFESIONAL
            html_popup = f"""
            <div style="font-family: sans-serif; min-width: 200px; color: #333;">
                <h4 style="margin-bottom: 5px; color: #007bff;">Vuelo: {callsign}</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;"><td><b>País:</b></td><td>{pais}</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Altitud:</b></td><td>{altitud} m</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Velocidad:</b></td><td>{velocidad} km/h</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Rumbo:</b></td><td>{rumbo}°</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Ascenso:</b></td><td>{v_vertical} m/s</td></tr>
                </table>
                <p style="font-size: 10px; margin-top: 10px; color: gray;">Haz clic fuera para cerrar</p>
            </div>
            """
            
            icon_html = f'''<div style="transform: rotate({rumbo}deg); color: #00FF00; font-size: 18px; cursor: pointer;">✈</div>'''
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html_popup, max_width=300),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # 3. CAPTURAR EL MOVIMIENTO DEL USUARIO
    map_data = st_folium(m, width="100%", height=600, key="mapa_principal")

    # Guardar posición si el usuario mueve el mapa
    if map_data and 'center' in map_data and map_data['center'] is not None:
        st.session_state['map_center'] = [map_data['center']['lat'], map_data['center']['lng']]
    if map_data and 'zoom' in map_data and map_data['zoom'] is not None:
        st.session_state['map_zoom'] = map_data['zoom']

else:
    st.error("📡 Buscando señal de satélite...")