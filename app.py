import streamlit as st
import requests
import os
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation

# Chargement des variables d'environnement
load_dotenv()
GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

st.title("📍 Géolocalisez-moi")

# --- Initialisation du Session State ---
if "location_triggered" not in st.session_state:
    st.session_state.location_triggered = False
    st.session_state.location_data = None

# --- 1. Le bouton ---
if st.button("📍 Géolocalisez-moi !"):
    st.session_state.location_triggered = True
    st.session_state.location_data = None
    st.info("⏳ Tentative de récupération de la position... (Veuillez autoriser dans votre navigateur)")

# --- 2. Déclencheur ---
if st.session_state.location_triggered:
    location = get_geolocation()
    print("🧩 Données brutes :", location)
    
    if location is None:
        st.info("⏳ En attente de la localisation… veuillez autoriser la géolocalisation dans le navigateur.")
    else:
        st.session_state.location_data = location
        st.session_state.location_triggered = False

# --- 3. Traitement des données ---
if st.session_state.location_data:
    location = st.session_state.location_data

    # Gestion des erreurs GPS
    if location.get("PERMISSION_DENIED"):
        st.error("❌ Permission refusée par l'utilisateur. Veuillez autoriser la géolocalisation dans votre navigateur.")
    elif location.get("POSITION_UNAVAILABLE"):
        st.error("❌ Position GPS indisponible. Vérifiez que votre appareil a le GPS activé.")
    elif isinstance(location, dict) and "coords" in location:
        coords = location["coords"]
        lat = coords.get("latitude")
        lon = coords.get("longitude")

        if lat is None or lon is None:
            st.warning("⚠️ Coordonnées incomplètes reçues.")
            st.json(coords)
        else:
            st.success(f"✅ Coordonnées : {lat}, {lon}")

            # Vérification clé API
            if not GMAPS_API_KEY:
                st.error("❌ Clé API Google absente. Vérifiez votre fichier .env ou les Secrets Streamlit.")
            else:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GMAPS_API_KEY}"
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("status") == "OK" and data.get("results"):
                        adresse = data["results"][0]["formatted_address"]
                        st.info(f"🏠 Adresse : {adresse}")
                        st.map([{"lat": float(lat), "lon": float(lon)}])
                        
                        # Lien Google Maps cliquable
                        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        st.markdown(f"[📍 Voir sur Google Maps]({google_maps_url})", unsafe_allow_html=True)
                    else:
                        st.error(f"⚠️ API Google n'a pas renvoyé de résultat. Statut: {data.get('status')}")
                        st.json(data)
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Erreur lors de l'appel à l'API Google : {e}")
                    print(f"❌ Erreur requests: {e}")
    else:
        st.error("🚨 Format inattendu de get_geolocation().")
        st.json(location)
