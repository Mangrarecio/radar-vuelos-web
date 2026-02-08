import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. Configuración de pantalla completa y tema oscuro
st.set_page_config(page_title="Radar Pro - España", layout="wide")

# 2. AUTO-REFRESCO: Se actualiza solo cada 30 segundos
st_autorefresh(interval=30000, key="datarefresh")

st.title("🛰️ Estación de Control Aéreo - Tiempo Real")
st.markdown("Sector: **Península Ibérica** | Actualización: Cada 30 seg.")

# 3. Función optimizada para descargar datos
def obtener_vuelos():
    url = "https://opensky-network.org/api/states/all?lamin=34.0&lomin=-10.0&lamax=44.5&lomax=4.5"
    try:
        r = requests.get(url, timeout=10)
        datos = r.json()
        columnas = ['icao24', 'callsign', 'pais', 'tiempo', 'contacto', 'long', 'lat', 'altitud', 'suelo', 'velocidad', 'rumbo']
        df = pd.DataFrame([fila[:11] for fila in datos['states']], columns=columnas)
        df['callsign'] = df['callsign'].str.strip()
        return df
    except:
        return None

df = obtener_vuelos()

if df is not None:
    # Métricas en la parte superior
    c1, c2, c3 = st.columns(3)
    c1.metric("Aviones Detectados", len(df))
    c2.metric("Velocidad Máxima", f"{int(df['velocidad'].max() * 3.6)} km/h")
    c3.metric("Altitud Media", f"{int(df['altitud'].mean())} m")

    # 4. Mapa Profesional (Estilo Oscuro)
    # Usamos CartoDB dark_matter para que parezca una pantalla de radar
    m = folium.Map(location=[40.41, -3.70], zoom_start=6, tiles="CartoDB dark_matter")

    for _, v in df.iterrows():
        if v['lat'] and v['long']:
            # Creamos un icono de avión que rota según su rumbo real
            icon_html = f'''<div style="transform: rotate({v['rumbo']}deg); color: #00FF00; font-size: 15px;">✈</div>'''
            
            folium.Marker(
                [v['lat'], v['long']],
                popup=f"Vuelo: {v['callsign']} | Alt: {v['altitud']}m",
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)

    # Mostrar mapa
    st_folium(m, width="100%", height=550)

    # 5. Tabla detallada plegable
    with st.expander("Ver Registro Detallado"):
        st.dataframe(df[['callsign', 'pais', 'altitud', 'velocidad', 'rumbo']], use_container_width=True)

else:
    st.warning("📡 Buscando señal de satélite... Reintenta en unos segundos.")