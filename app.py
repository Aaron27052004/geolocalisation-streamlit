import streamlit as st
import requests
import os
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium

# --- Chargement et Configuration ---
load_dotenv()
GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")
st.set_page_config(layout="wide") # Mettre la page en mode large
st.title("📍 Géolocalisation Interactive")

# --- Initialisation du Session State ---
# 'coords' est notre "source de vérité"
if "coords" not in st.session_state:
    st.session_state.coords = None
    st.session_state.address = None

# 'location_triggered' gère l'appel JS asynchrone
if "location_triggered" not in st.session_state:
    st.session_state.location_triggered = False

# --- Colonnes pour l'affichage ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Trouver votre position")
    
    # --- 1. Le bouton ---
    if st.button("📍 Géolocalisez-moi !"):
        st.session_state.location_triggered = True
        st.info("⏳ Récupération de la localisation...")

    # --- 2. Déclencheur (pour get_geolocation) ---
    if st.session_state.location_triggered:
        location = get_geolocation()
        print("🧩 Données brutes :", location)
        
        if location is None:
            st.info("⏳ En attente... veuillez autoriser la géolocalisation dans le navigateur.")
        else:
            st.session_state.location_triggered = False # On a reçu une réponse
            
            if location.get("PERMISSION_DENIED"):
                st.error("❌ Permission refusée.")
            elif location.get("POSITION_UNAVAILABLE"):
                st.error("❌ Position GPS indisponible.")
            elif isinstance(location, dict) and "coords" in location:
                lat = location["coords"].get("latitude")
                lon = location["coords"].get("longitude")
                if lat and lon:
                    # On met à jour notre "source de vérité"
                    st.session_state.coords = {"lat": lat, "lon": lon}
                else:
                    st.warning("⚠️ Coordonnées incomplètes reçues.")
            else:
                st.error("🚨 Format inattendu de get_geolocation().")

    # --- 3. Traitement des coordonnées (si elles existent) ---
    st.subheader("2. Adresse trouvée")
    
    # Cette partie s'exécute dès que st.session_state.coords est mis à jour
    # (soit par le bouton, soit par la carte)
    if st.session_state.coords:
        lat = st.session_state.coords["lat"]
        lon = st.session_state.coords["lon"]
        
        st.success(f"**Coordonnées :** `{lat}, {lon}`")

        if not GMAPS_API_KEY:
            st.error("❌ Clé API Google absente.")
        else:
            url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GMAPS_API_KEY}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK" and data.get("results"):
                    adresse = data["results"][0]["formatted_address"]
                    st.session_state.address = adresse # Sauvegarde pour l'info-bulle
                    st.info(f"**🏠 Adresse :** {adresse}")
                else:
                    st.error(f"⚠️ API Google n'a pas renvoyé de résultat.")
                    st.session_state.address = "Adresse introuvable"
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erreur lors de l'appel à l'API Google : {e}")

# --- 4. Affichage de la carte interactive ---
with col2:
    st.subheader("3. Ajuster sur la carte")
    st.write("Si la position n'est pas exacte, cliquez sur la carte pour la corriger.")

    # Définir un centre par défaut (Paris) si aucune coordonnée n'est encore définie
    DEFAULT_CENTER = [48.8566, 2.3522]
    map_center = [st.session_state.coords["lat"], st.session_state.coords["lon"]] if st.session_state.coords else DEFAULT_CENTER

    # === MODIFICATION MINIMALE ===
    # Créer la carte Folium avec la VUE SATELLITE
    m = folium.Map(
        location=map_center, 
        zoom_start=25,
        tiles='Esri WorldImagery', # Vue satellite par défaut
        name='Satellite'
    )

    
    # === FIN MODIFICATION ===

    # Ajouter un marqueur si les coordonnées existent
    if st.session_state.coords:
        tooltip = st.session_state.address or f"Lat: {st.session_state.coords['lat']:.5f}, Lon: {st.session_state.coords['lon']:.5f}"
        folium.Marker(
            [st.session_state.coords["lat"], st.session_state.coords["lon"]],
            tooltip=tooltip,
            popup=tooltip
        ).add_to(m)

    # AJOUT: Sélecteur de couches (pour basculer Satellite/Rues)
    folium.LayerControl().add_to(m)

    # Afficher la carte dans Streamlit et récupérer les interactions
    # 'last_clicked' est la clé !
    map_data = st_folium(m, center=map_center, width=700, height=500)

    # --- 5. Gérer le clic sur la carte ---
    if map_data and map_data.get("last_clicked"):
        new_lat = map_data["last_clicked"]["lat"]
        new_lon = map_data["last_clicked"]["lng"]
        
        # Vérifier si le clic est VRAIMENT un nouveau point
        # (pour éviter les re-chargements inutiles)
        if not st.session_state.coords or \
           (st.session_state.coords and \
           (st.session_state.coords["lat"] != new_lat or st.session_state.coords["lon"] != new_lon)):
            
            print(f"🖱️ Clic détecté : {new_lat}, {new_lon}")
            # On met à jour la "source de vérité"
            st.session_state.coords = {"lat": new_lat, "lon": new_lon}
            # On force le re-chargement pour que la "Partie 3" s'exécute
            st.rerun()