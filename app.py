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

# Actualización cada 2 minutos
st_autorefresh(interval=120000, key="datarefresh")

st.title("🌍 Radar de Vuelos Satelital")

# --- PANEL LATERAL ---
st.sidebar.header("🔍 Control de Radar")
busqueda_input = st.sidebar.text_input("Introduce CallSign (ej: IBE2622):", key="search_box").upper().strip()

if st.sidebar.button("🔄 Forzar Actualización / Mostrar Todos"):
    st.session_state.search_box = ""
    st.cache_data.clear() # Limpiamos la memoria para traer datos nuevos sí o sí
    st.rerun()

@st.cache_data(ttl=110)
def obtener_vuelos():
    # Coordenadas de España
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        # Añadimos un 'User-Agent' para que la API no nos bloquee pensando que somos un robot
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states'] is not None:
                columnas = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([fila[:12] for fila in datos['states']], columns=columnas)
                df['callsign'] = df['callsign'].str.strip()
                return df
        return None
    except Exception as e:
        return None

df = obtener_vuelos()

# --- LÓGICA DE VISUALIZACIÓN ---
if df is not None and not df.empty:
    df_mostrar = df[df['callsign'].str.contains(busqueda_input, na=False)] if busqueda_input else df

    # Mapa con Vista Satélite ESRI
    m = folium.Map(
        location=st.session_state['map_center'], 
        zoom_start=st.session_state['map_zoom'], 
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )

    for _, v in df_mostrar.iterrows():
        if not pd.isna(v['lat']) and not pd.isna(v['long']):
            call = v['callsign'] if v['callsign'] else "S/N"
            alt = int(v['altitud']) if not pd.isna(v['altitud']) else 0
            vel = int(v['velocidad'] * 3.6) if not pd.isna(v['velocidad']) else 0
            rumb = int(v['rumbo']) if not pd.isna(v['rumbo']) else 0
            
            html_popup = f"""
            <div style="width: 180px; font-family: sans-serif;">
                <b style="color: #e67e22;">✈ {call}</b><hr style="margin:5px 0;">
                <b>Altitud:</b> {alt} m<br>
                <b>Velocidad:</b> {vel} km/h<br>
                <b>País:</b> {v['pais']}
            </div>
            """
            
            # Icono blanco para que resalte sobre el satélite oscuro
            icon_html = f'''<div style="transform: rotate({rumb}deg); color: #00FF00; font-size: 20px; text-shadow: 1px 1px 2px black;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=folium.Popup(html_popup, max_width=250),
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    output = st_folium(m, width="100%", height=600, key="mapa_sat", returned_objects=["zoom", "center"])

    if output:
        if output.get('center'): st.session_state['map_center'] = [output['center']['lat'], output['center']['lng']]
        if output.get('zoom'): st.session_state['map_zoom'] = output['zoom']

    st.success(f"Radar Activo: {len(df_mostrar)} aviones detectados.")

else:
    # Si llega aquí es que la API está saturada o no hay datos
    st.warning("📡 El satélite está ocupado o no hay vuelos en este sector ahora mismo.")
    st.info("La API gratuita de OpenSky a veces limita las peticiones. Espera 1 minuto o pulsa el botón de reintento en el lateral.")
    if st.button("Reintentar Conexión"):
        st.cache_data.clear()
        st.rerun()