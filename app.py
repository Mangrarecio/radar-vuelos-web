import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. CONFIGURACIÓN INICIAL (Fuera del flujo de refresco para estabilidad)
if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Pro Estable", layout="wide")

# 2. ACTUALIZACIÓN CADA 2 MINUTOS (120000ms)
st_autorefresh(interval=120000, key="datarefresh")

st.title("🛰️ Radar de Vuelos (Modo Estable)")

# Panel Lateral
st.sidebar.header("Panel de Búsqueda")
busqueda = st.sidebar.text_input("🔍 Buscar Vuelo:", "").upper().strip()

@st.cache_data(ttl=110) # Cacheamos los datos un poco menos del tiempo de refresco
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
    # Filtro
    df_mostrar = df[df['callsign'].str.contains(busqueda, na=False)] if busqueda else df

    # --- MAPA ESTABILIZADO ---
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles="CartoDB dark_matter",
        zoom_control=True
    )

    for _, v in df_mostrar.iterrows():
        if not pd.isna(v['lat']) and not pd.isna(v['long']):
            try:
                alt = int(v['altitud']) if not pd.isna(v['altitud']) else 0
                vel = int(v['velocidad'] * 3.6) if not pd.isna(v['velocidad']) else 0
                rumb = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
                call = v['callsign'] if not pd.isna(v['callsign']) else "???"
                
                html_popup = f"<b>Vuelo:</b> {call}<br><b>Alt:</b> {alt}m<br><b>Vel:</b> {vel}km/h"
                icon_html = f'''<div style="transform: rotate({rumb}deg); color: #00FF00; font-size: 20px;">✈</div>'''
                
                folium.Marker(
                    [v['lat'], v['long']],
                    popup=folium.Popup(html_popup, max_width=200),
                    icon=folium.DivIcon(html=icon_html)
                ).add_to(m)
            except:
                continue

    # 3. RENDERIZADO CON CONTROL DE ESTADO
    # 'returned_objects' vacío ayuda a que no refresque por cada micro-movimiento
    output = st_folium(
        m, 
        width="100%", 
        height=600, 
        key="mapa_estable",
        returned_objects=["zoom", "center"] # Solo pedimos estos dos datos de vuelta
    )

    # Actualizar sesión solo si hay cambios reales para evitar bucles de parpadeo
    if output:
        if output.get('center') and output['center'] != st.session_state['map_center']:
            st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
        if output.get('zoom') and output['zoom'] != st.session_state['map_zoom']:
            st.session_state['map_zoom'] = output['zoom']

    st.caption(f"Sincronizado con radar: {pd.Timestamp.now().strftime('%H:%M:%S')}")
else:
    st.warning("Reconectando con el servidor de vuelos...")