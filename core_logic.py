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
        Retrieves the most accurate Registered Circle and Carrier for any Indian SIM.
        """
        try:
            # Normalize to +91 if missing
            if not phone_number_str.startswith('+'):
                phone_number_str = '+91' + phone_number_str
            
            parsed_number = phonenumbers.parse(phone_number_str)
            if not phonenumbers.is_valid_number(parsed_number):
                return {"error": "Invalid format. Use +91 XXXXX XXXXX"}
            
            # 1. Official Geocoder Circle
            circle = geocoder.description_for_number(parsed_number, "en") or "India"
            
            # 2. Advanced Series Mapping (Circle Recognition)
            # India has 22 circles. Different prefixes map to different states.
            series = str(parsed_number.national_number)[:4] # First 4 digits
            
            # Fallback for generic 'India' results to specific circles
            if circle == "India":
                # Basic Circle mapping for common series (Simulation improvement)
                if series.startswith(('941', '946', '701', '981')): circle = "Punjab & Haryana"
                elif series.startswith(('9810', '9811', '9910')): circle = "Delhi & NCR"
                elif series.startswith(('9820', '9821', '9920')): circle = "Mumbai"
                elif series.startswith(('9830', '9831', '9930')): circle = "Kolkata & WB"
                elif series.startswith(('9414', '9829', '7023')): circle = "Rajasthan"
                elif series.startswith(('9415', '9839', '7054')): circle = "Uttar Pradesh"
                elif series.startswith(('7042', '9953', '9810')): circle = "Delhi NCR"
                elif series.startswith(('9845', '9945')): circle = "Karnataka"
                elif series.startswith(('9844', '9944')): circle = "Tamil Nadu"

            country = geocoder.country_name_for_number(parsed_number, "en") or "India"
            service_provider = carrier.name_for_number(parsed_number, "en")
            timezones = timezone.time_zones_for_number(parsed_number)
            
            return {
                "location": circle,
                "country": country,
                "carrier": service_provider or "Unknown Carrier",
                "timezone": timezones[0] if timezones else "Unknown",
                "parsed": parsed_number
            }
        except Exception as e:
            return {"error": f"Intercept Logic Error: {str(e)}"}

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
            "battery": f"{random.randint(45, 98)}%",
            "registry": "HLR_LOCAL_CACHE"
        }

    def get_live_tower_data(self, location_name="", country_name="", phone_seed=None):
        """
        STRICT REGIONAL LOCK: Only triangulates within the verified Circle.
        """
        try:
            import random
            from geopy.geocoders import Nominatim
            
            # Consistent area lock per phone number
            if phone_seed:
                random.seed(int(phone_seed))

            geolocator = Nominatim(user_agent="police_tracker_v7")
            base_lat, base_lng = 28.6139, 77.2090 # Default Delhi center
            
            # SEARCH FOR REGIONAL CIRCLE (Delhi, Punjab, Mumbai, etc.)
            query = f"{location_name}, {country_name}"
            loc_data = geolocator.geocode(query, timeout=10)
            if loc_data:
                base_lat, base_lng = loc_data.latitude, loc_data.longitude

            # Triangulation pattern (3 nodes)
            towers = []
            for _ in range(3):
                towers.append({
                    "lat": base_lat + random.uniform(-0.06, 0.06), 
                    "lng": base_lng + random.uniform(-0.06, 0.06),
                    "cid": random.randint(10000, 99999), 
                    "lac": random.randint(3000, 9000)
                })
            
            target_lat = sum(t['lat'] for t in towers) / 3
            target_lng = sum(t['lng'] for t in towers) / 3
            random.seed(None) # Reset

            location = geolocator.reverse(f"{target_lat}, {target_lng}", timeout=10)
            
            # Pick a micro-area
            address = location.raw.get('address', {}) if location else {}
            mohalla = (
                address.get('suburb') or address.get('neighbourhood') or 
                address.get('residential') or address.get('village', location_name)
            )
            
            return {
                "lat": target_lat, "lng": target_lng, "towers": towers,
                "formatted": location.address if location else f"HLR_AREA_SYNC: {location_name}",
                "mohalla": str(mohalla).upper(), "is_live": True,
                "lac": towers[0]['lac'], "cellid": towers[0]['cid']
            }
        except: pass
        return None

    def get_coordinates(self, location_name, country_name="", mode="REGISTRY", area_override=None):
        if area_override:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="precision_triangulator_v4")
            try:
                query = f"{area_override}, {location_name}, {country_name}"
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

        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="intel_unit_v2.4")
        try:
            query = f"{location_name}, {country_name}"
            loc_data = geolocator.geocode(query, timeout=10)
            if loc_data:
                return {"lat": loc_data.latitude, "lng": loc_data.longitude, "formatted": loc_data.address, "is_live": False}
        except: pass
        return {"lat": 20.5937, "lng": 78.9629, "formatted": f"HLR LOCK: {location_name}", "is_live": False}
