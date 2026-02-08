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

# Estilo para que el mensaje de carga no sea tan invasivo
st.markdown("""<style> .stAlert { margin-top: -20px; } </style>""", unsafe_allow_html=True)

@st.cache_data(ttl=60) # Reducimos el tiempo de espera a 1 minuto
def obtener_vuelos_pro():
    # Coordenadas de España (Ajustadas)
    url = "https://opensky-network.org/api/states/all?lamin=35.0&lomin=-10.0&lamax=44.0&lomax=4.0"
    try:
        # Intentamos la conexión con tus credenciales
        r = requests.get(
            url, 
            auth=HTTPBasicAuth(USER_OPENSKY, PASS_OPENSKY), 
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if r.status_code == 200:
            datos = r.json()
            if datos and 'states' in datos and datos['states']:
                cols = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo', 'v_vertical']
                df = pd.DataFrame([f[:12] for f in datos['states']], columns=cols)
                df['callsign'] = df['callsign'].str.strip()
                return df, "Conexión Exitosa"
            else:
                return None, "No hay vuelos reportados en este momento"
        elif r.status_code == 429:
            return None, "API Saturada (Espera 60 seg)"
        else:
            return None, f"Error del servidor (Código {r.status_code})"
    except Exception as e:
        return None, f"Error de red: {str(e)}"

# --- EJECUCIÓN ---
st.title("🌍 Radar de Vuelos Satelital Pro")

df, status_msg = obtener_vuelos_pro()

# Panel lateral
st.sidebar.header("📡 Estado del Sistema")
st.sidebar.write(f"**Estado:** {status_msg}")
busqueda = st.sidebar.text_input("🔍 Filtrar Vuelo:", "").upper()

if st.sidebar.button("🔄 Forzar Reconexión"):
    st.cache_data.clear()
    st.rerun()

# --- DIBUJO DEL MAPA ---
# Si no hay datos, mostramos el mapa vacío centrado en España en lugar de un error
m = folium.Map(
    location=[40.41, -3.70], 
    zoom_start=6, 
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satélite'
)

if df is not None and not df.empty:
    df_filtrado = df[df['callsign'].str.contains(busqueda, na=False)] if busqueda else df
    
    for _, v in df_filtrado.iterrows():
        if v['lat'] and v['long']:
            alt = int(v['altitud']) if v['altitud'] else 0
            rumb = int(v['rumbo']) if v['rumbo'] else 0
            color = "#FF0000" if alt < 1000 else "#FFFF00" if alt < 5000 else "#00FF00"
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']} | Alt: {alt}m",
                icon=folium.DivIcon(html=f'<div style="transform: rotate({rumb}deg); color: {color}; font-size: 20px; text-shadow: 1px 1px 2px #000;">✈</div>')
            ).add_to(m)
    st.success(f"Detectadas {len(df_filtrado)} aeronaves.")
else:
    st.warning(f"⚠️ {status_msg}. Mostrando mapa base.")

# Renderizado del mapa (siempre se muestra)
st_folium(m, width="100%", height=600, key="mapa_v12")