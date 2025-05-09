import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import folium
from streamlit_folium import folium_static
import json
from branca.element import Figure

# Set page title and configuration
st.set_page_config(
    page_title="Fire Sensor Monitoring System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .sensor-normal { color: #4ade80; }
    .sensor-warning { color: #facc15; }
    .sensor-abnormal { color: #f87171; }
    .fire-alert { 
        background-color: #fee2e2; 
        border-left: 5px solid #ef4444;
        padding: 1rem;
        margin-bottom: 1rem;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }
    .evacuation-info {
        background-color: #dbeafe;
        border-left: 5px solid #3b82f6;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .dashboard-header {
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    .sensor-hover {
        font-weight: bold;
        background-color: #f3f4f6;
        padding: 0.5rem;
        border-radius: 0.25rem;
        transition: all 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# กำหนดพิกัดพื้นฐานของเขตป้อมปราบฯ
DISTRICT_COORDINATES = {
    "pomprap": [13.7539, 100.5156],  # พระนคร-ป้อมปราบ (Lat, Lng)
}

# ข้อมูลจุดเซนเซอร์ในเขตป้อมปราบฯ
pomprap_sensors = [
    {"id": 1, "name": "Sensor A1", "location": "Soi Nana - North", "coordinates": [13.7414, 100.5194], "status": "normal", "battery_level": 85},
    {"id": 2, "name": "Sensor A2", "location": "Yaowarat Road", "coordinates": [13.7393, 100.5129], "status": "normal", "battery_level": 72},
    {"id": 3, "name": "Sensor A3", "location": "Ratchadaphisek Road", "coordinates": [13.7354, 100.5154], "status": "normal", "battery_level": 90},
    {"id": 4, "name": "Sensor A4", "location": "Chakraphet Road", "coordinates": [13.7412, 100.5089], "status": "normal", "battery_level": 65},
    {"id": 5, "name": "Sensor A5", "location": "Charoen Krung Road", "coordinates": [13.7380, 100.5210], "status": "normal", "battery_level": 78},
    {"id": 6, "name": "Sensor A6", "location": "Pom Prap Market", "coordinates": [13.7380, 100.5129], "status": "normal", "battery_level": 55},
    {"id": 7, "name": "Sensor A7", "location": "Wat Saket Temple", "coordinates": [13.7401, 100.5175], "status": "normal", "battery_level": 82},
    {"id": 8, "name": "Sensor A8", "location": "Local School", "coordinates": [13.7365, 100.5165], "status": "normal", "battery_level": 93},
    {"id": 9, "name": "Sensor A9", "location": "Community Hospital", "coordinates": [13.7385, 100.5115], "status": "normal", "battery_level": 87},
    {"id": 10, "name": "Sensor A10", "location": "Shopping Center", "coordinates": [13.7425, 100.5145], "status": "normal", "battery_level": 71},
]

# รวมข้อมูลเซนเซอร์ตามพื้นที่
DISTRICT_SENSORS = {
    "pomprap": pomprap_sensors
}

# แปลงเป็น DataFrame เพื่อง่ายต่อการใช้งานใน Streamlit
def get_sensors_df(district, active_fire_sensor=None):
    sensors = DISTRICT_SENSORS.get(district, [])
    df = pd.DataFrame(sensors)
    
    # แยก coordinates เป็น lat, lon columns
    if not df.empty:
        df["lat"] = df["coordinates"].apply(lambda x: x[0])
        df["lon"] = df["coordinates"].apply(lambda x: x[1])
        
        # ถ้ามีเซนเซอร์ที่ตรวจพบไฟไหม้ ให้อัพเดทสถานะ
        if active_fire_sensor:
            df.loc[df["id"] == active_fire_sensor, "status"] = "abnormal"
    
    return df

# ฟังก์ชันสร้างแผนที่ด้วย Folium
def create_folium_map(district, sensors_df, active_fire_sensor=None, incident_location=None):
    # กำหนดตำแหน่งเริ่มต้นของแผนที่
    center = DISTRICT_COORDINATES.get(district, [13.7539, 100.5156])
    
    # สร้างแผนที่
    m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap")
    
    # เพิ่มเซนเซอร์ลงในแผนที่
    for _, sensor in sensors_df.iterrows():
        # กำหนดสีตามสถานะ
        if active_fire_sensor and sensor['id'] == active_fire_sensor:
            color = 'red'
            radius = 10
            fill_opacity = 0.8
            popup_html = f"""
            <div style='font-family: Arial; width: 200px;'>
                <h4 style='color: #d00; margin-bottom: 5px;'>{sensor['name']} - FIRE ALERT! 🔥</h4>
                <p><b>Location:</b> {sensor['location']}</p>
                <p><b>Status:</b> <span style='color: red; font-weight: bold;'>ABNORMAL</span></p>
                <p><b>Battery:</b> {sensor['battery_level']}%</p>
            </div>
            """
        else:
            if sensor['status'] == 'normal':
                color = 'green'
            elif sensor['status'] == 'warning':
                color = 'orange'
            else:
                color = 'red'
            radius = 6
            fill_opacity = 0.6
            popup_html = f"""
            <div style='font-family: Arial; width: 180px;'>
                <h4 style='margin-bottom: 5px;'>{sensor['name']}</h4>
                <p><b>Location:</b> {sensor['location']}</p>
                <p><b>Status:</b> <span style='color: {color}; font-weight: bold;'>{sensor['status'].upper()}</span></p>
                <p><b>Battery:</b> {sensor['battery_level']}%</p>
            </div>
            """
        
        folium.CircleMarker(
            location=[sensor['lat'], sensor['lon']],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            popup=folium.Popup(popup_html, max_width=200)
        ).add_to(m)
    
    # ถ้ามีเหตุการณ์ไฟไหม้ ให้เพิ่มวงกลมแสดงพื้นที่อพยพ
    if incident_location:
        folium.Circle(
            location=incident_location,
            radius=200,  # รัศมี 200 เมตร
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.2,
            popup='Evacuation Zone - 200m'
        ).add_to(m)
        
        # เพิ่มเครื่องหมายแสดงจุดเกิดเหตุ
        folium.Marker(
            location=incident_location,
            icon=folium.Icon(color='red', icon='fire', prefix='fa'),
            popup='Fire Incident Location'
        ).add_to(m)
    
    return m

# สร้าง sidebar
st.sidebar.title("ระบบเฝ้าระวังเพลิงไหม้")
st.sidebar.subheader("การตั้งค่า")

# เลือกเขตที่ต้องการแสดง
district = st.sidebar.selectbox(
    "เลือกเขต",
    options=list(DISTRICT_COORDINATES.keys()),
    format_func=lambda x: "เขตป้อมปราบศัตรูพ่าย" if x == "pomprap" else x,
    index=0
)

# สร้างเหตุการณ์จำลอง
simulate_fire = st.sidebar.checkbox("จำลองสถานการณ์ไฟไหม้", value=False)

# ถ้าเลือกจำลองไฟไหม้ ให้เลือกเซนเซอร์ที่ตรวจพบไฟ
active_fire_sensor = None
incident_location = None

if simulate_fire:
    sensor_options = {f"{s['name']} ({s['location']})": s['id'] for s in DISTRICT_SENSORS[district]}
    selected_sensor_key = st.sidebar.selectbox(
        "เลือกเซนเซอร์ที่ตรวจพบไฟ",
        options=list(sensor_options.keys())
    )
    active_fire_sensor = sensor_options[selected_sensor_key]
    
    # หาพิกัดของเซนเซอร์ที่เลือก
    for sensor in DISTRICT_SENSORS[district]:
        if sensor['id'] == active_fire_sensor:
            incident_location = sensor['coordinates']
            break

# ดึงข้อมูลเซนเซอร์
sensors_df = get_sensors_df(district, active_fire_sensor)

# สร้างหน้าหลัก
st.markdown("<h1 class='dashboard-header'>ระบบเฝ้าระวังเพลิงไหม้เขตป้อมปราบศัตรูพ่าย</h1>", unsafe_allow_html=True)

# แสดงการแจ้งเตือนถ้ามีการจำลองไฟไหม้
if simulate_fire and active_fire_sensor:
    selected_sensor = next((s for s in DISTRICT_SENSORS[district] if s['id'] == active_fire_sensor), None)
    
    if selected_sensor:
        st.markdown(f"""
        <div class='fire-alert'>
            <h2>🔥 พบการแจ้งเตือนไฟไหม้! 🔥</h2>
            <p><b>เซนเซอร์:</b> {selected_sensor['name']}</p>
            <p><b>สถานที่:</b> {selected_sensor['location']}</p>
            <p><b>สถานะ:</b> <span style='color: red; font-weight: bold;'>ABNORMAL</span></p>
            <p><b>เวลาที่ตรวจพบ:</b> {pd.Timestamp.now().strftime('%H:%M:%S')}</p>
        </div>
        
        <div class='evacuation-info'>
            <h3>ข้อมูลการอพยพ</h3>
            <p>กรุณาอพยพประชาชนในรัศมี 200 เมตรจากจุดเกิดเหตุ</p>
            <p>จุดอพยพที่ใกล้ที่สุด: โรงเรียนประจำชุมชน</p>
            <p>หมายเลขติดต่อฉุกเฉิน: 199 (ดับเพลิง), 1669 (หน่วยแพทย์ฉุกเฉิน)</p>
        </div>
        """, unsafe_allow_html=True)

# สร้างเค้าโครงหน้าจอ
col1, col2 = st.columns([2, 1])

# แสดงแผนที่ในคอลัมน์ที่ 1
with col1:
    st.subheader("แผนที่แสดงตำแหน่งเซนเซอร์")
    
    # สร้างแผนที่ด้วย Folium
    m = create_folium_map(district, sensors_df, active_fire_sensor, incident_location)
    
    # แสดงแผนที่
    folium_static(m, width=700, height=500)

# แสดงรายการเซนเซอร์ในคอลัมน์ที่ 2
with col2:
    st.subheader("รายการเซนเซอร์")
    
    # วนลูปแสดงข้อมูลเซนเซอร์
    for _, sensor in sensors_df.iterrows():
        # กำหนดสีตามสถานะ
        if active_fire_sensor and sensor['id'] == active_fire_sensor:
            status_style = "abnormal"
            status_text = "ABNORMAL"
            emoji = "🔥"
        else:
            status_style = sensor['status']
            status_text = sensor['status'].upper()
            emoji = "✅" if sensor['status'] == "normal" else "⚠️" if sensor['status'] == "warning" else "❌"
        
        # แสดงข้อมูลเซนเซอร์
        st.markdown(f"""
        <div class="sensor-card" id="sensor-{sensor['id']}">
            <p><b>{emoji} {sensor['name']}</b> - {sensor['location']}</p>
            <p>สถานะ: <span class="sensor-{status_style}">{status_text}</span></p>
            <p>แบตเตอรี่: {sensor['battery_level']}%</p>
            <hr>
        </div>
        """, unsafe_allow_html=True)

# แสดงข้อมูลสถิติด้านล่าง
st.subheader("สถิติการทำงานของเซนเซอร์")

# สร้างเมตริกสำหรับแสดงสถิติ
status_counts = sensors_df['status'].value_counts()
normal_count = status_counts.get('normal', 0)
warning_count = status_counts.get('warning', 0)
abnormal_count = status_counts.get('abnormal', 0)
total_sensors = len(sensors_df)

# แสดงสถิติในรูปแบบของเมตริก
metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("เซนเซอร์ทั้งหมด", total_sensors)
with metric_cols[1]:
    st.metric("ปกติ", normal_count, f"{normal_count/total_sensors*100:.1f}%")
with metric_cols[2]:
    st.metric("เตือน", warning_count, f"{warning_count/total_sensors*100:.1f}%")
with metric_cols[3]:
    st.metric("ผิดปกติ", abnormal_count, f"{abnormal_count/total_sensors*100:.1f}%")

# แสดงข้อมูลระดับแบตเตอรี่
st.subheader("ระดับแบตเตอรี่ของเซนเซอร์")

# สร้างกราฟแท่งแสดงระดับแบตเตอรี่
battery_data = sensors_df[['name', 'battery_level']].sort_values('battery_level')
st.bar_chart(battery_data.set_index('name'))

# แสดงข้อมูลการใช้งาน
st.markdown("""
### วิธีใช้งาน
1. ใช้ sidebar ด้านซ้ายเพื่อเลือกเขตที่ต้องการตรวจสอบ
2. สามารถจำลองสถานการณ์ไฟไหม้ได้โดยเลือก "จำลองสถานการณ์ไฟไหม้"
3. คลิกที่จุดเซนเซอร์บนแผนที่เพื่อดูรายละเอียด
4. สีของจุดเซนเซอร์แสดงสถานะ: เขียว (ปกติ), เหลือง (เตือน), แดง (ผิดปกติ)

### หมายเหตุ
ข้อมูลนี้เป็นการจำลองเพื่อการทดสอบระบบเท่านั้น
""")

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("© 2025 ระบบเฝ้าระวังเพลิงไหม้เขตป้อมปราบศัตรูพ่าย", unsafe_allow_html=True)