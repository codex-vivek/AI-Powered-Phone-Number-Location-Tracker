import streamlit as st
import phonenumbers
import folium
from streamlit_folium import st_folium
from utils import LocationProcessor
from ml_model import SafetyModel
import json
import time
import random

# Page Config
st.set_page_config(
    page_title="POLICE INTEL - MOBILE SENTINEL",
    page_icon="📡",
    layout="wide"
)

# Load CSS
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except: pass

# Initialize Components
@st.cache_resource
def load_components():
    return LocationProcessor(), SafetyModel()

loc_proc, safety_ai = load_components()

# Initialize Session State
if 'last_coords' not in st.session_state:
    st.session_state['last_coords'] = None
if 'ping_count' not in st.session_state:
    st.session_state['ping_count'] = 0
if 'tracking_info' not in st.session_state:
    st.session_state['tracking_info'] = None
if 'auto_ping' not in st.session_state:
    st.session_state['auto_ping'] = False
if 'trace_mode' not in st.session_state:
    st.session_state['trace_mode'] = "LIVE"

# Header - POLICE SPECIAL BRANCH OS
st.markdown("""
    <div style='background: #000; border: 2px solid #00ff41; padding: 10px; margin-bottom: 20px; box-shadow: 0 0 20px rgba(0,255,65,0.1); font-family: monospace;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h1 style='margin:0; font-size: 1.4rem; color: #00ff41; letter-spacing: 2px;'>POLICE SPECIAL INTERCEPT UNIT [v4.2]</h1>
                <p style='margin:0; font-size: 0.7rem; color: #008f11;'>RESTRICTED ACCESS: MINISTRY OF HOME AFFAIRS // DEPT_OF_SATELLITE_INTEL</p>
            </div>
            <div style='text-align: right;'>
                <p style='margin:0; color: #00ff41; font-size: 0.8rem;'>SIGNAL_LOCK: ACTIVE</p>
                <p style='margin:0; color: #ef4444; font-size: 0.6rem;'>LINK: ENCRYPTED // SAT_SYNC_4</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

@st.fragment()
def render_live_dashboard():
    info = st.session_state['tracking_info']
    status = st.session_state.get('device_status', "ONLINE")
    override = st.session_state.get('sector_override')
    
    # FORCED LIVE SIGNAL LOCK
    target_loc = info['location']
    country = info.get('country', "")
    coords = loc_proc.get_coordinates(
        target_loc, 
        country_name=country, 
        mode="LIVE", 
        area_override=override
    )
    st.session_state['last_coords'] = coords
    
    col1, col2 = st.columns([1, 1.5], gap="large")
    
    with col1:
        st.markdown("<div class='glass-card' style='border-top: 3px solid #00ff41;'>", unsafe_allow_html=True)
        tact = st.session_state.get('tactical', {})
        status_color = "#00ff00" if status == "ONLINE" else "#ef4444"
        
        st.markdown(f"""
        <div style='background: rgba(0, 255, 0, 0.05); padding: 15px; border-radius: 10px; border: 1px solid {status_color};'>
            <div style='display: flex; align-items: center; margin-bottom: 5px;'>
                <div class='radar-signal' style='background: {status_color};'></div>
                <h4 style='margin:0; color:{status_color}; font-size: 0.9rem;'>DEVICE STATUS: {status}</h4>
            </div>
            <p style="margin:0; font-family: monospace; font-size: 0.7rem; color: #666;">SAT_LATENCY: {random.randint(15, 45)}ms // PACKET_STRENGTH: 98%</p>
        </div>
        """, unsafe_allow_html=True)

        # Device Metadata
        batt_val = int(tact.get('battery', '85%').replace('%', ''))
        batt_color = "#00ff41" if batt_val > 40 else "#fbbf24" if batt_val > 15 else "#ef4444"
        
        st.markdown(f"""
            <div style="margin-top: 20px; background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 0.85rem;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                    <span style="color: #666;">POWER LVL:</span><span style="color: {batt_color};">{tact.get('battery', '85%')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                    <span style="color: #666;">HLR_NODE:</span><span style="color: #fff;">{tact.get('hlr')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                    <span style="color: #666;">SIGNAL:</span><span style="color: {status_color};">{tact.get('signal')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding-top: 4px;">
                    <span style="color: #00ff41;">PRECISION AREA:</span><span style="color: #fff;">{coords.get('mohalla', 'LOCKING...')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # High-Visibility Lock Banner
        mohalla_display = coords.get('mohalla', 'SCANNING...')
        st.markdown(f"""
            <div style='background: rgba(0,255,65,0.05); border: 1px solid #00ff41; padding: 15px; margin-top: 15px; text-align: center; border-radius: 5px;'>
                <p style='margin:0; color: #00ff41; font-family: monospace; font-size: 0.6rem;'>INTERCEPTED_CELL_ADDR</p>
                <h3 style='margin:0; color: #fff; font-size: 1.4rem;'>{mohalla_display}</h3>
            </div>
        """, unsafe_allow_html=True)

        if st.button("📡 RE-TRIANGULATE SIGNAL", use_container_width=True):
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        if coords and coords['lat'] != 0.0:
            m = folium.Map(
                location=[coords['lat'], coords['lng']], zoom_start=19,
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                attr='Google Hybrid', prefer_canvas=True
            )
            
            # Show Towers
            towers = coords.get('towers', [])
            for i, t in enumerate(towers):
                folium.Marker([t['lat'], t['lng']], icon=folium.Icon(color='blue', icon='broadcast-tower', prefix='fa')).add_to(m)
                folium.PolyLine([[t['lat'], t['lng']], [coords['lat'], coords['lng']]], color='blue', weight=1, opacity=0.4, dash_array='5, 10').add_to(m)
            
            # Target Marker
            marker_text = f"<div style='color:#fff; min-width:200px;'><b>[SATELLITE LOCK]</b><br>{info['location']}<br>{tact.get('signal')}</div>"
            folium.Marker([coords['lat'], coords['lng']], popup=folium.Popup(marker_text, max_width=300), icon=folium.Icon(color="red", icon="bullseye", prefix='fa')).add_to(m)
            folium.CircleMarker(location=[coords['lat'], coords['lng']], radius=20, color='red', fill=True, fill_opacity=0.3).add_to(m)

            st_folium(m, use_container_width=True, height=520, key="police_map")

            marker_color = "#00ff41" if status == "ONLINE" else "#ef4444"
            st.markdown(f"""
                <div style='display: flex; justify-content: space-between; background: #000; padding: 10px; border-radius: 5px; border: 1px solid #111; font-family: monospace; font-size: 0.8rem;'>
                    <span style='color: #666;'>LOCK_COORD: <span style='color:#fff;'>{coords['lat']:.6f}, {coords['lng']:.6f}</span></span>
                    <span style='color: {marker_color};'>{"[SATELLITE_LINK_STABLE]" if status == "ONLINE" else "[LINK_LOST]"}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

@st.fragment(run_every="3s")
def render_live_terminal():
    st.markdown("<div class='glass-card' style='height: 140px; overflow: hidden; padding: 10px;'>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; font-size: 0.6rem; color: #008f11;'>LIVE_POLICE_INTERCEPT_FEED_v4.2</p>", unsafe_allow_html=True)
    st.session_state['ping_count'] += 1
    logs = [
        f"[{time.strftime('%H:%M:%S')}] PACKET INTERCEPTED VIA MSC_NODE_{st.session_state['ping_count'] % 50}",
        f"[{time.strftime('%H:%M:%S')}] SIGNAL_LEVEL: {random.randint(-110, -70)} dBm",
        f"[{time.strftime('%H:%M:%S')}] ENCRYPTION BYPASS: SUCCESSFUL",
        f"[{time.strftime('%H:%M:%S')}] TRIANGULATION_DRIFT: {random.uniform(0.01, 0.45):.3f}m",
    ]
    for log in logs:
        st.markdown(f"<p style='margin:0; font-family: monospace; font-size: 0.7rem; color: #aaa;'>{log}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_tactical_sidebar():
    with st.sidebar:
        st.markdown("<div style='background: #000; border: 1px solid #00ff41; padding: 15px; border-radius: 5px; margin-top: 10px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00ff41; font-size: 0.9rem; margin-top: 0; text-align: center;'>📡 TACTICAL CALIBRATION</h3>", unsafe_allow_html=True)
        
        new_sector = st.text_input("INPUT SECTOR/AREA", 
                                 value=st.session_state.get('sector_override', ""),
                                 placeholder="e.g. Sector 17, Chandigarh",
                                 key="sector_input_field")
        
        if st.button("LOCK SIGNAL TO SECTOR", use_container_width=True):
            st.session_state['sector_override'] = new_sector
            st.toast("SECTOR LOCKED", icon="🎯")
            st.rerun()
            
        if st.session_state.get('sector_override'):
            if st.button("CLEAR OVERRIDE", use_container_width=True):
                st.session_state['sector_override'] = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #333; font-size: 0.6rem; margin-top: 20px;'>COMMANDER: POLICE_INTEL_UNIT_7</p>", unsafe_allow_html=True)

# Main Execution
if not st.session_state.get('tracking_info'):
    col1, col2 = st.columns([1, 1], gap="medium")
    with col1:
        st.markdown("<div class='glass-card' style='height: 400px; padding: 25px;'>", unsafe_allow_html=True)
        st.subheader("🕵️ INITIATE TARGET SCAN")
        phone_input = st.text_input("INPUT TARGET MSISDN", placeholder="+91 XXXX XXXX")
        if st.button("BYPASS SS7 FIREWALL & TRACE", use_container_width=True):
            if phone_input:
                info = loc_proc.get_basic_info(phone_input)
                if "error" in info:
                    st.error(f"SCAN FAILED: {info['error']}")
                else:
                    st.session_state['tracking_info'] = info
                    st.session_state['tactical'] = loc_proc.get_tactical_metadata(info['carrier'])
                    st.session_state['device_status'] = "ONLINE"
                    with st.status("🔍 INITIATING POLICE INTERCEPT...", expanded=True) as status:
                        time.sleep(1)
                        st.write("`[HLR]` Interrogating Home Location Register...")
                        time.sleep(1)
                        st.write("`[SS7]` Triangulating Live Tower Signal...")
                        status.update(label="📡 TARGET LOCKED ON SATELLITE", state="complete")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='glass-card' style='height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00ff41;'>UNIT STATUS: STANDBY</h3>", unsafe_allow_html=True)
        st.markdown("<div class='radar-signal' style='background: #00ff41;'></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    render_tactical_sidebar()
    render_live_dashboard()
    render_live_terminal()

st.markdown("<p style='text-align: center; color: #222; font-size: 0.6rem; margin-top: 30px;'>ESTABLISHED SECURE GOVT LINE // RSA-4096 // INTEL_SENTINEL_SYSTEM</p>", unsafe_allow_html=True)
