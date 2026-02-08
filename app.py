import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from requests.auth import HTTPBasicAuth

# --- CREDENCIALES INTEGRADAS ---
USER_OPENSKY = "mangrarecio"
PASS_OPENSKY = "Manga1234@"

if 'map_center' not in st.session_state:
    st.session_state['map_center'] = [40.41, -3.70]
if 'map_zoom' not in st.session_state:
    st.session_state['map_zoom'] = 6

st.set_page_config(page_title="Radar Satelital Premium", layout="wide")
st_autorefresh(interval=120000, key="datarefresh")

st.title("🌍 Radar de Vuelos Satelital (Cuenta Premium)")

# --- PANEL LATERAL ---
st.sidebar.header("🔍 Filtros de Radar")
busqueda_input = st.sidebar.text_input("Buscar Vuelo (CallSign):", key="search_box").upper().strip()

if st.sidebar.button("🔄 Forzar Actualización"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=110)
def obtener_vuelos():
    # Coordenadas de España
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        # Usamos tus credenciales para tener prioridad
        r = requests.get(
            url, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), 
            timeout=15
        )
        
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

# --- INTERFAZ ---
if df is not None and not df.empty:
    df_mostrar = df[df['callsign'].str.contains(busqueda_input, na=False)] if busqueda_input else df

    # Mapa Satelital
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )

    for _, v in df_mostrar.iterrows():
        if not pd.isna(v['lat']) and not pd.isna(v['long']):
            alt = int(v['altitud']) if not pd.isna(v['altitud']) else 0
            vel = int(v['velocidad'] * 3.6) if not pd.isna(v['velocidad']) else 0
            rumb = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
            
            html = f"""
            <div style="width: 180px; font-family: sans-serif;">
                <b style="color: #e67e22; font-size: 14px;">✈ {v['callsign']}</b><hr style="margin:5px 0;">
                <b>Altitud:</b> {alt} m<br>
                <b>Velocidad:</b> {vel} km/h<br>
                <b>País:</b> {v['pais']}
            </div>
            """
            
            # Icono con sombra para visibilidad total
            icon_html = f'''<div style="transform: rotate({rumb}deg); color: #00FF00; font-size: 22px; text-shadow: 2px 2px 3px #000;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=folium.Popup(html, max_width=250),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    output = st_folium(m, width="100%", height=600, key="mapa_v8", returned_objects=["zoom", "center"])

    if output:
        if output.get('center'): st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
        if output.get('zoom'): st.session_state['map_zoom'] = output['zoom']

    st.success(f"Conexión Estable: {len(df_mostrar)} aeronaves en pantalla.")

else:
    st.warning("📡 Sincronizando con OpenSky... Si tarda mucho, pulsa 'Forzar Actualización'.")