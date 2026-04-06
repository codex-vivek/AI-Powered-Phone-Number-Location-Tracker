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
    page_title="Autonomous Phone Tracker",
    page_icon="📡",
    layout="wide"
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Components
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

# Header - COMMAND CENTER OS
st.markdown("""
    <div style='background: #000; border: 2px solid #00ff41; padding: 10px; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h2 style='margin:0; font-size: 1.5rem; color: #00ff41;'>NATIONAL INTELLIGENCE INTERCEPT UNIT</h2>
                <p style='margin:0; font-size: 0.7rem; color: #00ff41;'>RESTRICTED ACCESS: POLICE SPECIAL BRANCH // LEVEL 7 CLEARANCE REQUIRED</p>
            </div>
            <div style='text-align: right;'>
                <p style='margin:0; font-family: monospace; color: #00ff41;'>SYS_LOG: ENCRYPTED</p>
                <p style='margin:0; font-family: monospace; color: #00ff41;'>LOC_SRV: ACTIVE [NORTH_SATELLITE_4]</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

@st.fragment()
def render_live_dashboard():
    info = st.session_state['tracking_info']
    status = st.session_state.get('device_status', "ONLINE")
    mode = st.session_state.get('trace_mode', "LIVE")
    override = st.session_state.get('sector_override')
    
    # FORCED LIVE SIGNAL LOCK with Optional Manual Override
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
        
        # Display Stats
        status_color = "#00ff00" if status == "ONLINE" else "#ef4444"
        st.markdown(f"""
        <div style='background: rgba(0, 255, 0, 0.05); padding: 15px; border-radius: 10px; border: 1px solid {status_color};'>
            <div style='display: flex; align-items: center; margin-bottom: 10px;'>
                <div class='radar-signal' style='background: {status_color};'></div>
                <h4 style='margin:0; color:{status_color};'>DEVICE STATUS: {status}</h4>
            </div>
            <p style="margin:0; font-family: monospace; font-size: 0.8rem; color: {status_color};">LIVE PACKET STREAM: {"RECEIVED" if status == "ONLINE" else "SIGNAL LOST"}</p>
        </div>
        """, unsafe_allow_html=True)

        if status == "OFFLINE / SWITCHED OFF":
            st.warning("⚠️ TARGET DEVICE IS POWERED OFF. DISPLAYING LAST KNOWN LOCATION FROM CARRIER HLR CACHE.")

        # Device Metadata
        # Dynamic color for battery
        batt_val = int(tact.get('battery', '85%').replace('%', ''))
        batt_color = "#00ff41" if batt_val > 40 else "#fbbf24" if batt_val > 15 else "#ef4444"
        
        st.markdown(f"""
            <div style="margin-top: 20px; background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 0.85rem;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                    <span style="color: #666;">POWER STATUS:</span><span style="color: {batt_color}; font-weight: bold;">{tact.get('battery', '85%')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                    <span style="color: #666;">LAC / CELL-ID:</span><span style="color: #fff;">{tact.get('lac')} / {tact.get('cellid')}</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #111; padding: 4px 0;">
                     <span style="color: #666;">SIGNAL Strength:</span><span style="color: {status_color}; text-shadow: 0 0 5px {status_color};">{tact.get('signal')}</span>
                 </div>
                 <div style="display: flex; justify-content: space-between; padding-top: 4px;">
                     <span style="color: #666;">DETECTED MOHALLA:</span><span style="color: #00ff41; font-weight: bold;">{coords.get('mohalla', 'SCANNING...')}</span>
                 </div>
             </div>
        """, unsafe_allow_html=True)

        # Intelligence Report
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1)'>", unsafe_allow_html=True)
        st.subheader("🕵️ INTELLIGENCE LOGS")
        
        safety_report = safety_ai.predict_safety(info['parsed'])
        behavior_report = safety_ai.analyze_behavior(tact)
        
        with st.expander("OPEN CASE FILE", expanded=False):
            st.markdown(f"`[REPORT]` NETWORK RISK: **{safety_report['score']}%**")
            st.markdown(f"`[REPORT]` DEVICE THREAT: **{behavior_report['threat_score']}%**")
            st.markdown(f"`[CLASS]` {safety_report['category']}")
            st.markdown("---")
            st.markdown("**Device Signature Alerts:**")
            if status != "ONLINE":
                st.code("ALERT: Device is powered off. Signal intercept unavailable.")
            for alert in behavior_report['alerts']:
                st.code(f"ALERT: {alert}")
            st.markdown("**Network Logic Events:**")
            for reason in safety_report['reasons']:
                st.code(f"EVENT: {reason}")

        st.success("🛰️ SS7 CORE INTERCEPT ACTIVE (DIRECT TOWER ACCESS)")
        
        # High-Visibility Mohalla Lock Banner
        mohalla_display = coords.get('mohalla', 'SCANNING...')
        st.markdown(f"""
            <div style='background: rgba(0,255,65,0.1); border-left: 5px solid #00ff41; padding: 15px; margin-top: 10px; margin-bottom: 10px;'>
                <h4 style='margin:0; color: #00ff41; font-family: monospace; font-size: 0.7rem;'>🎯 TARGET AREA LOCKED</h4>
                <h2 style='margin:0; color: #fff; font-size: 1.6rem; letter-spacing: 2px;'>{mohalla_display}</h2>
            </div>
        """, unsafe_allow_html=True)

        if st.button("📡 RE-TRIANGULATE SIGNAL"):
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        st.subheader("🗺️ AUTONOMOUS SATELLITE MAP")
        
        if coords and coords['lat'] != 0.0:
            m = folium.Map(
                location=[coords['lat'], coords['lng']], 
                zoom_start=19, # FORENSIC ZOOM (Level 19)
                tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                attr='Google Hybrid Intelligence',
                prefer_canvas=True
            )
            
            # Show Active Triangulation Towers
            towers = coords.get('towers', [])
            for i, t in enumerate(towers):
                # Tower Marker
                folium.Marker(
                    [t['lat'], t['lng']], 
                    icon=folium.Icon(color='blue', icon='broadcast-tower', prefix='fa'),
                    tooltip=f"TOWER_{i+1} [LAC:{t['lac']} CID:{t['cid']}]"
                ).add_to(m)
                
                # Triangulation Line (Dashed)
                folium.PolyLine(
                    [[t['lat'], t['lng']], [coords['lat'], coords['lng']]], 
                    color='blue', 
                    weight=1, 
                    opacity=0.6, 
                    dash_array='8, 8'
                ).add_to(m)
                
            # Draw Movement Trail
            if len(st.session_state['move_history']) > 1:
                folium.PolyLine(
                    st.session_state['move_history'],
                    color="#00ff41",
                    weight=4,
                    opacity=0.8
                ).add_to(m)

            # Target Identity Marker
            addr_data = coords.get('mohalla', 'LIVE_NODE')
            target_name = info.get('carrier', 'UNKNOWN')
            full_addr = coords.get('formatted', '')
            
            marker_text = f"""
                <div style='font-family: monospace; color: #fff; min-width: 250px;'>
                    <b style='color: #ef4444; font-size: 1.1rem;'>[LIVE TARGET LOCK]</b><br>
                    <hr style='border-color: #333; margin: 5px 0;'>
                    <b>MSISDN:</b> {phonenumbers.format_number(info['parsed'], phonenumbers.PhoneNumberFormat.INTERNATIONAL) if info.get('parsed') else 'N/A'}<br>
                    <b>CARRIER:</b> {target_name}<br>
                    <b>LAC:</b> {coords.get('lac')} | <b>CID:</b> {coords.get('cellid')}<br>
                    <b>BATT:</b> {tact.get('battery')} | <b>SIG:</b> {tact.get('signal')}<br>
                    <b>MOHALLA:</b> {addr_data}<br>
                    <b style='color: #00ff41;'>ADDR:</b> <span style='font-size: 0.75rem;'>{full_addr[:80]}</span>
                </div>
            """
            
            folium.Marker(
                [coords['lat'], coords['lng']], 
                popup=folium.Popup(marker_text, max_width=400),
                tooltip=f"📍 TARGET AREA: {addr_data}",
                icon=folium.Icon(color="red", icon="bullseye", prefix='fa')
            ).add_to(m)
            
            # Pulse effect (Live position)
            folium.CircleMarker(
                location=[coords['lat'], coords['lng']],
                radius=15,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.4
            ).add_to(m)
            
            folium.Circle(
                radius=40,
                location=[coords['lat'], coords['lng']],
                color="#00ff00" if status == "ONLINE" else "#ef4444",
                fill=True,
                fill_opacity=0.3
            ).add_to(m)

            st_folium(m, use_container_width=True, height=550, key="autonomous_map", returned_objects=[])

            # Footer Tactical Stats
            marker_color = "#00ff41" if status == "ONLINE" else "#ef4444"
            lock_text = "[AUTONOMOUS LOCK]" if status == "ONLINE" else "[HLR CACHE LOCK]"
            ping_status = f"DATA RECEIVED ({st.session_state['ping_count']})" if status == "ONLINE" else "SIGNAL LOST - CACHED DATA"
            
            st.markdown(f"""
                <div style='display: flex; justify-content: space-between; background: #000; padding: 0.8rem; border-radius: 10px; border: 1px solid {marker_color};'>
                    <div style='font-family: monospace;'>
                        <p style='margin:0; color: {marker_color}; font-size: 0.7rem;'>{lock_text}</p>
                        <p style='margin:0; font-size: 0.9rem; color: #fff;'>COORD: {coords['lat']:.6f}, {coords['lng']:.6f}</p>
                    </div>
                    <div style='text-align: right; font-family: monospace;'>
                        <p style='margin:0; color: #94a3b8; font-size: 0.7rem;'>SATELLITE SYNC</p>
                        <p style='margin:0; font-size: 0.8rem; color: {marker_color};'>{ping_status}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"<div style='height: 2px; width: 100%; background: #111; margin-top: 5px;'><div style='height: 100%; width: 100%; background: {marker_color}; opacity: 0.3;'></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

def render_tactical_sidebar():
    with st.sidebar:
        st.markdown("<div style='background: #000; border: 1px solid #00ff41; padding: 15px; border-radius: 5px; margin-top: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00ff41; font-size: 0.9rem; margin-top: 0;'>📡 TACTICAL OVERRIDE</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.7rem; color: #666;'>If automatic triangulation is offset, manually calibrate the sector below.</p>", unsafe_allow_html=True)
        
        # Use a key to prevent reset on manual interaction
        new_sector = st.text_input("CALIBRATE SECTOR (PHASE/BLOCK)", 
                                 value=st.session_state.get('sector_override', ""),
                                 placeholder="e.g. Phase 3B2, Mohali",
                                 key="sector_input_field")
        
        if st.button("UPDATE SECTOR LOCK"):
            st.session_state['sector_override'] = new_sector
            st.rerun()
        
        if st.session_state.get('sector_override'):
            if st.button("CLEAR OVERRIDE"):
                st.session_state['sector_override'] = None
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Main Execution Logic
if not st.session_state.get('tracking_info'):
    col1, col2 = st.columns([1.5, 1], gap="small")
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📡 INITIATE TARGET SCAN")
        phone_input = st.text_input("INPUT TARGET MSISDN", placeholder="+91 XXXX XXXX")
        if st.button("BYPASS CARRIER FIREWALL & TRACE"):
            if phone_input:
                info = loc_proc.get_basic_info(phone_input)
                if "error" in info:
                    st.error(f"SCAN FAILED: {info['error']}")
                else:
                    st.session_state['tracking_info'] = info
                    st.session_state['tactical'] = loc_proc.get_tactical_metadata(info['carrier'])
                    st.session_state['last_coords'] = None
                    st.session_state['device_status'] = "ONLINE"
                    st.session_state['auto_ping'] = True
                    st.session_state['move_history'] = []
                    with st.status("�️ BYPASSING SS7 PROTOCOL...", expanded=True) as status:
                        time.sleep(1)
                        st.write("`[LOG]` Injecting exploit into HLR database...")
                        time.sleep(1)
                        st.write("`[LOG]` Intercepting signal from nearest MSC...")
                        status.update(label="BYPASS SUCCESSFUL - TARGET LOCKED", state="complete")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='glass-card' style='height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #00ff41;'>UNIT STATUS: READY</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.8rem;'>AWAITING TARGET MSISDN FOR INTERCEPTION</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # Tracking Mode
    render_tactical_sidebar()
    render_live_dashboard()
    
    # Live Terminal Sub-Fragment
    @st.fragment(run_every="3s")
    def render_live_terminal():
        st.markdown("<div class='glass-card' style='height: 150px; overflow: hidden; padding-top: 5px;'>", unsafe_allow_html=True)
        st.markdown("<p style='margin:0; font-size: 0.7rem; color: #00ff41; border-bottom: 1px solid #00ff41;'>LIVE SS7 PACKET INTERCEPT STREAM</p>", unsafe_allow_html=True)
        
        # Increment ping for simulation effect
        st.session_state['ping_count'] += 1
        
        # Simulate a scrolling log
        logs = [
            f"[{time.strftime('%H:%M:%S')}] PACKET RECEIVED FROM MSC_IND_{st.session_state['ping_count'] % 99}",
            f"[{time.strftime('%H:%M:%S')}] IMEI CHECK_SUM: VALIDATED",
            f"[{time.strftime('%H:%M:%S')}] SIGNAL_LEVEL: {random.randint(-110, -70)} dBm",
            f"[{time.strftime('%H:%M:%S')}] CIPHER_MODE: A5/1 (INTERCEPTED)",
            f"[{time.strftime('%H:%M:%S')}] TRIANGULATION_OFFSET: {random.uniform(0.1, 0.9):.3f}m",
        ]
        for log in logs:
            st.markdown(f"<p style='margin:0; font-family: monospace; font-size: 0.7rem;'>{log}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_live_terminal()

# Footer
st.markdown("<p style='text-align: center; color: #006400; font-size: 0.7rem;'>SECURED GOVT LINE // ENCRYPTED VIA RSA-4096 // POLICE_UNIT_INTEL</p>", unsafe_allow_html=True)
