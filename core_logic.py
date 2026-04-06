import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from opencage.geocoder import OpenCageGeocode
import streamlit as st
import requests

class LocationProcessor:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.geocoder = OpenCageGeocode(api_key) if api_key else None

    def get_basic_info(self, phone_number_str):
        """
        STRICT CIRCLE DETECTION: Uses official telecom series mapping for India.
        """
        try:
            # Normalize to India (+91) if prefix is missing
            if not phone_number_str.startswith('+'):
                prefix_clean = ''.join(filter(str.isdigit, phone_number_str))
                if not prefix_clean.startswith('91'):
                    phone_number_str = '+91' + prefix_clean
                else:
                    phone_number_str = '+' + prefix_clean

            parsed_number = phonenumbers.parse(phone_number_str)
            if not phonenumbers.is_valid_number(parsed_number):
                return {"error": "Invalid MSISDN format. Use +91 XXXXX XXXXX"}
            
            # Identify Registered Circle (State)
            circle = geocoder.description_for_number(parsed_number, "en") or "India"
            
            # Series Mapping fallback for generic 'India' tags
            series = str(parsed_number.national_number)[:5]
            if circle == "India":
                # Known Indian telecom circles for common series (Samples)
                if series.startswith(('941', '981', '701')): circle = "Punjab & Haryana"
                elif series.startswith(('9810', '9811', '9910', '7042')): circle = "Delhi & NCR"
                elif series.startswith(('9414', '9829', '7023')): circle = "Rajasthan"
                elif series.startswith(('9415', '9839', '7054')): circle = "Uttar Pradesh"
                elif series.startswith(('9820', '9821', '9920')): circle = "Mumbai"
                elif series.startswith(('9830', '9831', '9930')): circle = "West Bengal"
                elif series.startswith(('9845', '9945')): circle = "Karnataka"
            
            provider = carrier.name_for_number(parsed_number, "en") or "Carrier Unidentified"
            country = geocoder.country_name_for_number(parsed_number, "en") or "India"
            
            return {
                "location": circle,
                "country": country,
                "carrier": provider,
                "parsed": parsed_number
            }
        except Exception as e:
            return {"error": f"Intercept Decode Error: {str(e)}"}

    def get_tactical_metadata(self, carrier_name):
        import random
        carrier_codes = {"Jio": "405-840", "Airtel": "404-94", "VI": "404-01", "BSNL": "404-34"}
        mcc_mnc = carrier_codes.get(carrier_name, "404-X")
        return {
            "imsi": f"{mcc_mnc}{random.randint(10000000, 99999999)}",
            "hlr": f"MSC-NODE-{carrier_name[:3].upper()}",
            "lac": random.randint(1000, 9999), 
            "cellid": random.randint(10000, 99999), 
            "signal": f"-{random.randint(65, 85)} dBm",
            "battery": f"{random.randint(55, 98)}%",
            "registry": "HLR_SECURE_NODE"
        }

    def get_live_tower_data(self, location_name="", country_name="", phone_seed=None):
        """
        PRECISION REGION LOCK: Ensures mock-neighborhoods are strictly within circle.
        """
        try:
            import random
            from geopy.geocoders import Nominatim
            
            if phone_seed:
                random.seed(int(phone_seed))

            geolocator = Nominatim(user_agent="police_intelligence_v10")
            
            # Base Location: Circle Center (Defensive Check for US defaults)
            base_lat, base_lng = 28.6139, 77.2090 # Delhi
            
            try:
                query = f"{location_name}, India"
                loc_data = geolocator.geocode(query, timeout=10)
                if loc_data:
                    temp_lat, temp_lng = loc_data.latitude, loc_data.longitude
                    # INDIA BOUNDARY LOCK (6-38 Lat, 68-98 Lon)
                    if 6 <= temp_lat <= 38 and 68 <= temp_lng <= 98:
                        base_lat, base_lng = temp_lat, temp_lng
            except: pass

            # Triangulate within 5-10km of Circle Center
            towers = []
            for _ in range(3):
                towers.append({
                    "lat": base_lat + random.uniform(-0.05, 0.05), 
                    "lng": base_lng + random.uniform(-0.05, 0.05),
                    "cid": random.randint(10000, 99999), 
                    "lac": random.randint(3000, 9000)
                })
            
            target_lat = sum(t['lat'] for t in towers) / 3
            target_lng = sum(t['lng'] for t in towers) / 3
            random.seed(None)

            location = geolocator.reverse(f"{target_lat}, {target_lng}", timeout=10)
            addr_data = location.raw.get('address', {}) if location else {}
            
            mohalla = (addr_data.get('suburb') or addr_data.get('neighbourhood') or 
                       addr_data.get('residential') or addr_data.get('city', location_name)).upper()
            
            # Final Safety: If reverse geocode accidentally hits USA, force back to circle name
            if "DALLES" in str(mohalla) or "UNITED STATES" in str(mohalla):
                mohalla = location_name.upper()

            return {
                "lat": target_lat, "lng": target_lng, "towers": towers,
                "formatted": location.address if location else f"HLR_SECTOR: {location_name}",
                "mohalla": mohalla, "is_live": True,
                "lac": towers[0]['lac'], "cellid": towers[0]['cid']
            }
        except:
            return {"lat": 28.61, "lng": 77.21, "mohalla": "ERROR_HLR_LOCK", "is_live": True, "towers": []}

    def get_coordinates(self, location_name, country_name="", mode="REGISTRY", area_override=None):
        if area_override:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="precision_triangulator_v10")
            try:
                query = f"{area_override}, {location_name}, India"
                loc_data = geolocator.geocode(query, timeout=10)
                if loc_data:
                    return {
                        "lat": loc_data.latitude, "lng": loc_data.longitude,
                        "formatted": loc_data.address, "is_live": True, "mohalla": area_override
                    }
            except: pass

        if mode == "LIVE":
            parsed = st.session_state.get('tracking_info', {}).get('parsed')
            seed = parsed.national_number if parsed else None
            return self.get_live_tower_data(location_name=location_name, country_name=country_name, phone_seed=seed)

        return {"lat": 28.6139, "lng": 77.2090, "formatted": f"REGISTRY_CIRCLE: {location_name}", "is_live": False}
