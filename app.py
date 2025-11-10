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
# On l'utilise pour mémoriser l'état de notre demande
if "location_triggered" not in st.session_state:
    st.session_state.location_triggered = False
    st.session_state.location_data = None

# --- 1. Le bouton ---
# Le bouton ne fait qu'une chose : "lever un drapeau"
if st.button("📍 Géolocalisez-moi !"):
    st.session_state.location_triggered = True
    st.session_state.location_data = None # On reset les vieilles données
    st.info("⏳ Tentative de récupération de la position... (Veuillez autoriser dans votre navigateur)")

# --- 2. Le déclencheur ---
# Cette partie s'exécute à CHAQUE rerun du script
# Si le drapeau est levé...
if st.session_state.location_triggered:
    
    # On appelle get_geolocation()
    # Au 1er run (juste après clic), location = None
    # Au 2e run (après retour JS), location = {données}
    location = get_geolocation()
    print("🧩 Données brutes :", location)

    # Si on a enfin reçu des données...
    if location:
        # On sauvegarde les données
        st.session_state.location_data = location
        # On baisse le drapeau (tâche accomplie !)
        st.session_state.location_triggered = False

# --- 3. Traitement des données ---
# Cette partie est séparée. Elle s'exécute dès que des données sont dispo.
if st.session_state.location_data:
    
    location = st.session_state.location_data # On récupère les données
    
    # Gérer le cas où l'utilisateur refuse
    if location.get("PERMISSION_DENIED"):
        st.error("❌ Vous avez refusé la permission de géolocalisation.")
        print("❌ PERMISSION_DENIED")
        st.session_state.location_data = None # Nettoyage

    # Gérer le cas où la position est introuvable
    elif location.get("POSITION_UNAVAILABLE"):
        st.error("❌ Position non disponible.")
        print("❌ POSITION_UNAVAILABLE")
        st.session_state.location_data = None # Nettoyage

    # Si tout est bon (on a les coords)
    elif isinstance(location, dict) and "coords" in location:
        coords = location["coords"]
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        print("🌍 Latitude :", lat, "Longitude :", lon)

        if lat and lon:
            st.success(f"✅ Coordonnées : {lat}, {lon}")
            
            # Vérification que la clé API est bien chargée
            if not GMAPS_API_KEY:
                st.error("❌ Clé API Google (GMAPS_API_KEY) non trouvée. Vérifiez votre fichier .env")
                print("❌ GMAPS_API_KEY est None")
            else:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GMAPS_API_KEY}"
                
                try:
                    response = requests.get(url)
                    response.raise_for_status() # Lève une erreur si HTTP 4xx ou 5xx
                    data = response.json()
                    print("📦 Réponse API Google :", data)

                    if data.get("status") == "OK":
                        adresse = data["results"][0]["formatted_address"]
                        st.info(f"🏠 Adresse : {adresse}")
                        st.map([{"lat": float(lat), "lon": float(lon)}])
                    else:
                        st.error(f"⚠️ API Google n'a pas renvoyé de résultat. Statut: {data.get('status')}")
                        print("⚠️ Status API Google :", data.get("status"), "Message:", data.get("error_message"))
                
                except requests.exceptions.RequestException as e:
                    st.error(f"Erreur lors de l'appel à l'API Google: {e}")
                    print(f"❌ Erreur requests: {e}")
        else:
            st.warning("⚠️ Coordonnées incomplètes reçues.")
            print("⚠️ latitude ou longitude manquante :", coords)
    
    # Gérer un format inconnu
    else:
        st.error("🚨 Format inattendu de get_geolocation().")
        print("🚨 Format inattendu :", location)
        st.json(location) # Affiche le dict pour débugger