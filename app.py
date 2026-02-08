import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. MEMORIA DE LA PÁGINA (Session State)
# Esto evita que el mapa se resetee al actualizar
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
        # Cogemos las primeras 12 columnas
        df = pd.DataFrame([fila[:12] for fila in datos['states']], columns=columnas)
        df['callsign'] = df['callsign'].str.strip()
        return df
    except:
        return None

df = obtener_vuelos()

if df is not None:
    # --- CREACIÓN DEL MAPA ---
    # Usamos los valores guardados en la "memoria" (session_state)
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles="CartoDB dark_matter"
    )

    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            # 2. VENTANA EMERGENTE PROFESIONAL (HTML)
            # Aquí diseñamos la ventanita que verás al hacer clic
            html_popup = f"""
            <div style="font-family: sans-serif; min-width: 200px; color: #333;">
                <h4 style="margin-bottom: 5px; color: #007bff;">Vuelo: {v['callsign']}</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #eee;"><td><b>País:</b></td><td>{v['pais']}</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Altitud:</b></td><td>{int(v['altitud'])} m</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Velocidad:</b></td><td>{int(v['velocidad']*3.6)} km/h</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Rumbo:</b></td><td>{int(v['rumbo'])}°</td></tr>
                    <tr style="border-bottom: 1px solid #eee;"><td><b>Ascenso:</b></td><td>{v['v_vertical']} m/s</td></tr>
                    <tr><td><b>ID Transpondedor:</b></td><td><code>{v['icao24']}</code></td></tr>
                </table>
                <p style="font-size: 10px; margin-top: 10px; color: gray;">Haz clic en la X para cerrar</p>
            </div>
            """
            
            icon_html = f'''<div style="transform: rotate({v['rumbo']}deg); color: #00FF00; font-size: 18px; cursor: pointer;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=folium.Popup(html_popup, max_width=300),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # 3. CAPTURAR EL MOVIMIENTO DEL USUARIO
    # Esta función detecta si el usuario mueve el mapa o hace zoom
    map_data = st_folium(m, width="100%", height=600, key="mapa_principal")

    # Si el usuario movió el mapa, guardamos la nueva posición para la próxima actualización
    if map_data['last_object_clicked_popup'] is None: # Solo si no estamos interactuando con un popup
        if map_data['center'] is not None:
            st.session_state['map_center'] = [map_data['center']['lat'], map_data['center']['lng']]
        if map_data['zoom'] is not None:
            st.session_state['map_zoom'] = map_data['zoom']

    st.info("💡 Haz clic en cualquier avión para ver su hoja técnica. El mapa mantendrá tu posición al actualizarse.")

else:
    st.error("No se pudo recibir señal. Reintentando...")