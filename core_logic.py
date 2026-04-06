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
        try:
            if not phone_number_str.startswith('+'):
                phone_number_str = '+91' + phone_number_str
            
            parsed_number = phonenumbers.parse(phone_number_str)
            if not phonenumbers.is_valid_number(parsed_number):
                return {"error": "Invalid format. Use +91XXXXX XXXXX"}
            
            circle = geocoder.description_for_number(parsed_number, "en") or "India"
            country = geocoder.country_name_for_number(parsed_number, "en") or "India"
            service_provider = carrier.name_for_number(parsed_number, "en")
            
            return {
                "location": circle,
                "country": country,
                "carrier": service_provider or "Unknown Carrier",
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
        STRICT INDIA REGION LOCK (V9.0): 
        Physically prevents USA (The Dalles) coordinates from being returned.
        """
        try:
            import random
            from geopy.geocoders import Nominatim
            
            if phone_seed:
                random.seed(int(phone_seed))

            geolocator = Nominatim(user_agent="police_triangulator_v9_stable")
            
            # Default to Central India (Nagpur)
            base_lat, base_lng = 21.1458, 79.0882 
            
            try:
                # Search for the provided area/circle
                query = f"{location_name}, {country_name}"
                loc_data = geolocator.geocode(query, timeout=10)
                if loc_data:
                    temp_lat, temp_lng = loc_data.latitude, loc_data.longitude
                    
                    # HARD FAIL-SAFE: Check if the coordinates are outside India's box
                    # India is roughly between Lat 6-38 and Lon 68-98
                    # USA (The Dalles) is Lat 45, Lon -121. This check will kill it.
                    if (6 <= temp_lat <= 38) and (68 <= temp_lng <= 98):
                        base_lat, base_lng = temp_lat, temp_lng
                    else:
                        # If geocoder returns USA or server location, force back to Delhi center
                        base_lat, base_lng = 28.6139, 77.2090 
            except: 
                # Fallback to Delhi center if lookup fails
                base_lat, base_lng = 28.6139, 77.2090

            # Generate virtual towers within small radius
            towers = []
            for _ in range(3):
                towers.append({
                    "lat": base_lat + random.uniform(-0.04, 0.04), 
                    "lng": base_lng + random.uniform(-0.04, 0.04),
                    "cid": random.randint(10000, 99999), 
                    "lac": random.randint(3000, 9000)
                })
            
            target_lat = sum(t['lat'] for t in towers) / 3
            target_lng = sum(t['lng'] for t in towers) / 3
            random.seed(None)

            # Reverse geocode the simulated point
            location = geolocator.reverse(f"{target_lat}, {target_lng}", timeout=10)
            
            # Final check to ensure reverse geocoding doesn't flip back to "The Dalles"
            addr_str = str(location.address if location else "").upper()
            if "THE DALLES" in addr_str or "OREGON" in addr_str or "UNITED STATES" in addr_str:
                final_mohalla = location_name.upper()
                final_addr = f"SATELLITE INTERCEPT: {location_name}, INDIA"
            else:
                addr_data = location.raw.get('address', {}) if location else {}
                final_mohalla = (addr_data.get('suburb') or addr_data.get('neighbourhood') or 
                                 addr_data.get('residential') or addr_data.get('city', location_name)).upper()
                final_addr = location.address if location else f"HLR_NODE: {location_name}"

            return {
                "lat": target_lat, "lng": target_lng, "towers": towers,
                "formatted": final_addr,
                "mohalla": final_mohalla, "is_live": True,
                "lac": towers[0]['lac'], "cellid": towers[0]['cid']
            }
        except Exception as e:
            # Absolute fallback
            return {
                "lat": 28.6139, "lng": 77.2090, "mohalla": "DELHI_CENTER", 
                "formatted": "EMERGENCY_HLR_LOAD", "is_live": True, "towers": []
            }

    def get_coordinates(self, location_name, country_name="", mode="REGISTRY", area_override=None):
        if area_override:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="precision_triangulator_v9")
            try:
                query = f"{area_override}, {location_name}, {country_name}"
                loc_data = geolocator.geocode(query, timeout=10)
                if loc_data:
                    temp_lat, temp_lng = loc_data.latitude, loc_data.longitude
                    if (6 <= temp_lat <= 38) and (68 <= temp_lng <= 98):
                        return {
                            "lat": temp_lat, "lng": temp_lng,
                            "formatted": loc_data.address, "is_live": True, "mohalla": area_override
                        }
            except: pass

        if mode == "LIVE":
            parsed = st.session_state.get('tracking_info', {}).get('parsed')
            seed = parsed.national_number if parsed else None
            return self.get_live_tower_data(location_name=location_name, country_name=country_name, phone_seed=seed)

        return {"lat": 28.6139, "lng": 77.2090, "formatted": f"REGISTRY_CITY: {location_name}", "is_live": False}
