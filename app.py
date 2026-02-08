import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. MEMORIA DE LA PÁGINA (Para no perder el zoom)
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Pro + Buscador", layout="wide")

# 2. CONFIGURACIÓN DE ACTUALIZACIÓN (120000 ms = 2 Minutos)
st_autorefresh(interval=120000, key="datarefresh")

st.title("🛰️ Radar de Vuelos con Buscador")

# --- BARRA LATERAL (Panel de Control) ---
st.sidebar.header("Panel de Búsqueda")
# Buscador que convierte a mayúsculas automáticamente
busqueda = st.sidebar.text_input("🔍 Buscar por Código de Vuelo (Callsign):", "").upper().strip()

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
    # --- FILTRO DE BÚSQUEDA ---
    if busqueda:
        df_mostrar = df[df['callsign'].str.contains(busqueda, na=False)]
        st.sidebar.success(f"Encontrados: {len(df_mostrar)} avión/es")
    else:
        df_mostrar = df
        st.sidebar.info(f"Total en España: {len(df)} aviones")

    # --- MAPA ---
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles="CartoDB dark_matter"
    )

    for _, v in df_mostrar.iterrows():
        lat, lon = v['lat'], v['long']
        
        if not pd.isna(lat) and not pd.isna(lon):
            # Limpieza de datos segura
            callsign = v['callsign'] if not pd.isna(v['callsign']) else "???"
            try:
                alt = int(v['altitud']) if not pd.isna(v['altitud']) else 0
                vel = int(v['velocidad'] * 3.6) if not pd.isna(v['velocidad']) else 0
                rumb = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
            except:
                alt, vel, rumb = 0, 0, 0
                
            pais = v['pais'] if not pd.isna(v['pais']) else "N/A"

            # Ventana emergente con todos los datos
            html_popup = f"""
            <div style="font-family: sans-serif; min-width: 180px;">
                <h4 style="color: #007bff; margin: 0;">✈ {callsign}</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 2px 0;"><b>País:</b> {pais}</p>
                <p style="margin: 2px 0;"><b>Altitud:</b> {alt} m</p>
                <p style="margin: 2px 0;"><b>Velocidad:</b> {vel} km/h</p>
                <p style="margin: 2px 0;"><b>Rumbo:</b> {rumb}°</p>
            </div>
            """
            
            # Icono verde neón
            icon_html = f'''<div style="transform: rotate({rumb}deg); color: #00FF00; font-size: 20px;">✈</div>'''
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html_popup, max_width=300),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # Mostrar mapa
    output = st_folium(m, width="100%", height=600, key="mapa_v6")

    # Guardar estado para que no se mueva el zoom al actualizar
    if output and output.get('center'):
        st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
    if output and output.get('zoom'):
        st.session_state['map_zoom'] = output['zoom']

    st.caption(f"Última actualización: {pd.Timestamp.now().strftime('%H:%M:%S')} (Próxima en 2 min)")

else:
    st.error("📡 Error al conectar con OpenSky. Esperando respuesta...")