
import { useRef, useEffect, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

// กำหนดพิกัดพื้นฐานของเขตป้อมปราบฯ
const DISTRICT_COORDINATES: Record<string, [number, number]> = {
  pomprap: [100.5156, 13.7539], // พระนคร-ป้อมปราบ
};

// คำอธิบายพิกัดและชื่อจุดเซนเซอร์ตามแต่ละเขต
interface SensorLocation {
  id: number;
  name: string;
  location: string;
  coordinates: [number, number];
  status: "normal" | "warning" | "abnormal";
  batteryLevel?: number;
}

// ข้อมูลจุดเซนเซอร์ในเขตป้อมปราบฯ
const pomprapSensors: SensorLocation[] = [
  { id: 1, name: "Sensor A1", location: "Soi Nana - North", coordinates: [100.5194, 13.7414], status: "normal" },
  { id: 2, name: "Sensor A2", location: "Yaowarat Road", coordinates: [100.5129, 13.7393], status: "normal" },
  { id: 3, name: "Sensor A3", location: "Ratchadaphisek Road", coordinates: [100.5154, 13.7354], status: "normal" },
  { id: 4, name: "Sensor A4", location: "Chakraphet Road", coordinates: [100.5089, 13.7412], status: "normal" },
  { id: 5, name: "Sensor A5", location: "Charoen Krung Road", coordinates: [100.5210, 13.7380], status: "normal" },
  { id: 6, name: "Sensor A6", location: "Pom Prap Market", coordinates: [100.5129, 13.7380], status: "normal" },
  { id: 7, name: "Sensor A7", location: "Wat Saket Temple", coordinates: [100.5175, 13.7401], status: "normal" },
  { id: 8, name: "Sensor A8", location: "Local School", coordinates: [100.5165, 13.7365], status: "normal" },
  { id: 9, name: "Sensor A9", location: "Community Hospital", coordinates: [100.5115, 13.7385], status: "normal" },
  { id: 10, name: "Sensor A10", location: "Shopping Center", coordinates: [100.5145, 13.7425], status: "normal" },
];

// รวมข้อมูลเซนเซอร์ตามพื้นที่
const DISTRICT_SENSORS: Record<string, SensorLocation[]> = {
  pomprap: pomprapSensors,
};

// ค่าตั้งต้นของ Mapbox token
const MAPBOX_TOKEN = "YOUR_MAPBOX_TOKEN";

interface MapComponentProps {
  district: string;
  hasActiveIncident?: boolean;
  incidentLocation?: [number, number];
  activeFireSensor?: number;
  sensorLocations?: SensorLocation[];
  hoveredSensor?: number | null;
  onSensorHover?: (sensorId: number | null) => void;
}

const MapComponent = ({ 
  district, 
  hasActiveIncident = false,
  incidentLocation, 
  activeFireSensor,
  sensorLocations,
  hoveredSensor,
  onSensorHover
}: MapComponentProps) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markerRefs = useRef<Record<number, mapboxgl.Marker>>({});
  const [mapboxToken, setMapboxToken] = useState<string>(MAPBOX_TOKEN);
  const [mapLoaded, setMapLoaded] = useState(false);
  const styleRef = useRef<HTMLStyleElement | null>(null);
  
  // สำหรับในกรณีที่ยังไม่มี token
  const handleTokenChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setMapboxToken(event.target.value);
    localStorage.setItem("mapbox_token", event.target.value);
  };

  // โหลด token จาก localStorage (ถ้ามี)
  useEffect(() => {
    const savedToken = localStorage.getItem("mapbox_token");
    if (savedToken) {
      setMapboxToken(savedToken);
    }
  }, []);

  // Effect สำหรับอัพเดทสถานะ marker เมื่อมีการ hover
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    
    Object.values(markerRefs.current).forEach(marker => {
      const el = marker.getElement();
      el.classList.remove('hovered-sensor');
    });

    if (hoveredSensor !== null && markerRefs.current[hoveredSensor]) {
      const el = markerRefs.current[hoveredSensor].getElement();
      el.classList.add('hovered-sensor');
    }
  }, [hoveredSensor, mapLoaded]);

  useEffect(() => {
    if (!mapContainer.current || !mapboxToken || mapboxToken === "YOUR_MAPBOX_TOKEN") return;
    
    // เพิ่ม CSS สำหรับ animation ของ marker
    const style = document.createElement("style");
    style.innerHTML = `
      @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
      }
      @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
      }
      .hovered-sensor {
        z-index: 100 !important;
        transform: scale(1.5) !important;
        transition: transform 0.3s ease !important;
      }
      .fire-emoji {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 16px;
        animation: bounce 1s ease infinite;
      }
    `;
    document.head.appendChild(style);
    styleRef.current = style;

    // สร้างแผนที่
    mapboxgl.accessToken = mapboxToken;
    
    if (map.current) {
      map.current.remove();
    }
    
    const coordinates = DISTRICT_COORDINATES[district] || [100.5156, 13.7539]; // กำหนดค่าเริ่มต้นเป็นเขตป้อมปราบฯ
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: coordinates,
      zoom: 15,
    });

    // เพิ่ม controls
    map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

    // เมื่อแผนที่โหลดเสร็จให้เพิ่ม markers
    map.current.on("load", () => {
      setMapLoaded(true);
      
      // ใช้ข้อมูลเซนเซอร์ที่ได้รับ ถ้าไม่มีใช้ค่าเริ่มต้น
      const sensors = sensorLocations || DISTRICT_SENSORS[district] || [];
      
      // ล้าง markers เก่า
      Object.values(markerRefs.current).forEach(marker => marker.remove());
      markerRefs.current = {};
      
      // เพิ่ม markers สำหรับเซนเซอร์แต่ละตัว
      sensors.forEach(sensor => {
        // สร้าง DOM element สำหรับ marker
        const el = document.createElement("div");
        el.className = "sensor-marker";
        
        // กำหนดสีตามสถานะของเซนเซอร์หรือถ้าเป็นจุดที่มีไฟไหม้
        if (hasActiveIncident && sensor.id === activeFireSensor) {
          el.style.backgroundColor = "#ff0000"; // สีแดงสำหรับจุดที่มีไฟไหม้
          el.style.width = "20px";
          el.style.height = "20px";
          el.style.borderRadius = "50%";
          el.style.boxShadow = "0 0 10px 2px rgba(255, 0, 0, 0.6)";
          el.style.animation = "pulse 1.5s infinite";
          el.style.cursor = "pointer";
          el.style.transition = "transform 0.3s ease";
          
          // เพิ่ม emoji ไฟไหม้
          const fireEmoji = document.createElement("div");
          fireEmoji.className = "fire-emoji";
          fireEmoji.textContent = "🔥";
          el.appendChild(fireEmoji);
        } else {
          el.style.backgroundColor = sensor.status === "normal" ? "#4ade80" : 
                                    sensor.status === "warning" ? "#facc15" : "#f87171";
          el.style.width = "12px";
          el.style.height = "12px";
          el.style.borderRadius = "50%";
          el.style.border = "2px solid white";
          el.style.cursor = "pointer";
          el.style.transition = "transform 0.3s ease";
        }

        // Event listeners สำหรับ hover
        if (onSensorHover) {
          el.addEventListener('mouseenter', () => {
            onSensorHover(sensor.id);
          });
          
          el.addEventListener('mouseleave', () => {
            onSensorHover(null);
          });
        }

        // เพิ่ม marker ลงในแผนที่
        const marker = new mapboxgl.Marker(el)
          .setLngLat(sensor.coordinates)
          .setPopup(new mapboxgl.Popup({ offset: 25 }).setHTML(
            `<div>
              <strong>${sensor.name}</strong>
              <p>${sensor.location}</p>
              <p>Status: <span class="font-bold ${
                sensor.status === "normal" ? "text-green-600" : 
                sensor.status === "warning" ? "text-yellow-600" : "text-red-600"
              }">${sensor.status.toUpperCase()}</span></p>
              ${sensor.batteryLevel !== undefined ? 
                `<p>Battery: <span class="${sensor.batteryLevel < 20 ? "text-red-600 font-bold" : ""}">${sensor.batteryLevel}%</span></p>` : 
                ''}
            </div>`
          ))
          .addTo(map.current!);
          
        // เก็บ reference ไว้เพื่ออัพเดทภายหลัง
        markerRefs.current[sensor.id] = marker;
      });

      // แสดงวงกลมพื้นที่อพยพในกรณีมีเหตุการณ์ไฟไหม้
      if (hasActiveIncident && incidentLocation) {
        // ลบเลเยอร์เก่าถ้ามี
        if (map.current?.getLayer('evacuation-zone')) {
          map.current.removeLayer('evacuation-zone');
        }
        if (map.current?.getSource('evacuation-zone')) {
          map.current.removeSource('evacuation-zone');
        }
        
        // เพิ่มแหล่งข้อมูลและเลเยอร์สำหรับแสดงรัศมีอพยพ
        map.current?.addSource("evacuation-zone", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: incidentLocation
            },
            properties: {}
          }
        });

        // เพิ่มวงกลมแสดงพื้นที่อพยพ
        map.current?.addLayer({
          id: "evacuation-zone",
          type: "circle",
          source: "evacuation-zone",
          paint: {
            "circle-radius": 200,
            "circle-color": "#ff0000",
            "circle-opacity": 0.2,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ff0000",
            "circle-stroke-opacity": 0.6
          }
        });
        
        // ซูมไปที่จุดเกิดเหตุ
        map.current?.flyTo({
          center: incidentLocation,
          zoom: 16,
          essential: true
        });
      }
    });

    // Cleanup เมื่อคอมโพเนนต์ถูกทำลาย
    return () => {
      // Fixed: More careful cleanup to prevent errors
      if (styleRef.current) {
        try {
          document.head.removeChild(styleRef.current);
        } catch (e) {
          console.log("Style element already removed");
        }
      }
      
      // Fixed: More careful map cleanup
      if (map.current) {
        try {
          // Clear all markers first
          Object.values(markerRefs.current).forEach(marker => {
            try {
              marker.remove();
            } catch (e) {
              console.log("Error removing marker");
            }
          });
          
          // Remove map carefully
          map.current.remove();
        } catch (e) {
          console.log("Error during map cleanup:", e);
        }
      }
    };
  }, [district, mapboxToken, hasActiveIncident, activeFireSensor, incidentLocation, sensorLocations]);

  // ถ้ายังไม่มี token ให้แสดงฟอร์มสำหรับใส่ token
  if (!mapboxToken || mapboxToken === "YOUR_MAPBOX_TOKEN") {
    return (
      <div className="p-4 border rounded-md">
        <h3 className="text-lg font-medium mb-2">Mapbox Token Required</h3>
        <p className="text-sm text-muted-foreground mb-4">
          To display the map, you need to enter your Mapbox public token. You can get one by signing up at{" "}
          <a href="https://mapbox.com" target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">
            mapbox.com
          </a>
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 flex-1"
            placeholder="Enter your Mapbox public token"
            value={mapboxToken === "YOUR_MAPBOX_TOKEN" ? "" : mapboxToken}
            onChange={handleTokenChange}
          />
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Your token will be saved in your browser's local storage.
        </p>
      </div>
    );
  }

  return (
    <div className="aspect-video bg-muted relative rounded-md border overflow-hidden">
      <div ref={mapContainer} className="absolute inset-0" />
      {!mapLoaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p>กำลังโหลดแผนที่...</p>
        </div>
      )}
    </div>
  );
};

export default MapComponent;