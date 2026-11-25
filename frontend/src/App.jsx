import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FlyToInterpolator } from '@deck.gl/core';
import MapWrapper from './components/MapWrapper';
import AnalyticsPanel from './components/AnalyticsPanel';
import Navbar from './components/Navbar';
import MetricsBar from './components/MetricsBar';
import LayerControls from './components/LayerControls';
import { NAVI_MUMBAI_WARDS_GEOJSON } from './data/naviMumbaiGeoData';
import { MAHARASHTRA_DISTRICTS_GEOJSON } from './data/maharashtraGeoData';

// Initial Camera Viewport for Navi Mumbai (MVP Demonstration Core)
const INITIAL_VIEW_STATE = {
  longitude: 73.0297,
  latitude: 19.0330,
  zoom: 12.5,
  pitch: 50,
  bearing: 25,
  maxPitch: 85,
  minZoom: 3.5,
  maxZoom: 18,
};

// Preset Camera Viewports for Hierarchical Drill-Down
const PRESET_VIEW_STATES = {
  national: {
    longitude: 78.9629,
    latitude: 20.5937,
    zoom: 4.2,
    pitch: 0,
    bearing: 0,
    transitionDuration: 1800,
    transitionInterpolator: new FlyToInterpolator({ speed: 1.2, curve: 1.4 })
  },
  state: {
    longitude: 75.7139,
    latitude: 19.7515,
    zoom: 6.8,
    pitch: 32,
    bearing: -10,
    transitionDuration: 1800,
    transitionInterpolator: new FlyToInterpolator({ speed: 1.2, curve: 1.4 })
  },
  city: {
    longitude: 73.0297,
    latitude: 19.0330,
    zoom: 12.5,
    pitch: 50,
    bearing: 25,
    transitionDuration: 2000,
    transitionInterpolator: new FlyToInterpolator({ speed: 1.3, curve: 1.5 })
  }
};

export default function App() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [drillDownLevel, setDrillDownLevel] = useState('city'); // 'national' | 'state' | 'city' | 'ward'
  const [selectedFeature, setSelectedFeature] = useState(NAVI_MUMBAI_WARDS_GEOJSON.features[0]); // Default to Vashi
  const [metricMode, setMetricMode] = useState('water'); // 'water' | 'air' | 'composite'
  
  const [layerOptions, setLayerOptions] = useState({
    show3dColumns: true,
    showSensorNodes: true,
    showWireframes: true,
  });

  const [wsConnected, setWsConnected] = useState(false);
  const [telemetryData, setTelemetryData] = useState(null);
  const [historicalBuffer, setHistoricalBuffer] = useState([]);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  /**
   * Real-Time WebSocket Telemetry Connection Pipeline
   * Listens for 2s broadcasting from FastAPI backend.
   */
  useEffect(() => {
    const connectWebSocket = () => {
      // Determine WebSocket protocol & host
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname || 'localhost';
      const wsUrl = `${protocol}//${host}:8000/ws/environmental-data`;

      console.log(`[WebSocket] Connecting to ${wsUrl}...`);
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log('[WebSocket] Connection established to FastAPI engine.');
        setWsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setTelemetryData(payload);

          // Maintain rolling buffer of last 20 snapshots for sparklines
          setHistoricalBuffer((prev) => {
            const updated = [...prev, payload];
            if (updated.length > 20) updated.shift();
            return updated;
          });
        } catch (err) {
          console.error('[WebSocket] Failed to parse telemetry payload:', err);
        }
      };

      socket.onerror = (error) => {
        console.warn('[WebSocket] Error encountered, falling back to simulated stream:', error);
      };

      socket.onclose = () => {
        console.log('[WebSocket] Connection closed. Retrying in 3000ms...');
        setWsConnected(false);
        reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, []);

  /**
   * Client-Side Fallback Simulation Loop (If backend is offline or starting)
   * Guarantees 60 FPS animated visualization out of the box.
   */
  useEffect(() => {
    if (wsConnected) return; // Use real WebSocket when available

    const fallbackInterval = setInterval(() => {
      const now = Date.now() / 1000;
      setTelemetryData((prev) => {
        const seq = (prev?.sequence || 0) + 1;
        const mockWards = {};
        
        NAVI_MUMBAI_WARDS_GEOJSON.features.forEach((f) => {
          const id = f.properties.id;
          const baseBod = id === 'NM-MAHAPE' || id === 'NM-TALOJA' ? 15.0 : 8.0;
          const baseCod = id === 'NM-MAHAPE' || id === 'NM-TALOJA' ? 78.0 : 45.0;
          const noise = Math.sin(now + id.charCodeAt(3)) * 2.0;

          mockWards[id] = {
            bod: Math.max(3.0, +(baseBod + noise * 0.6).toFixed(1)),
            cod: Math.max(15.0, +(baseCod + noise * 2.2).toFixed(1)),
            do: Math.max(2.0, +(6.0 - noise * 0.3).toFixed(1)),
            ph: +(7.4 + noise * 0.05).toFixed(2),
            aqi: Math.max(50, Math.round(150 + noise * 12)),
            pm25: Math.max(20, +(68 + noise * 5).toFixed(1)),
            pm10: Math.max(40, +(130 + noise * 8).toFixed(1)),
            no2: +(38 + noise * 2).toFixed(1),
            water_flow_mld: +(280 + noise * 10).toFixed(0),
            status: baseBod > 12 ? 'CRITICAL' : 'NORMAL'
          };
        });

        const newPayload = {
          timestamp: now,
          sequence: seq,
          navi_mumbai_wards: mockWards,
          maharashtra_districts: {},
          states: {},
          active_alerts: seq % 3 === 0 ? [{
            id: `ALT-${seq}`,
            region_name: "Mahape MIDC",
            message: "Elevated Chemical Oxygen Demand (>80 mg/L) detected in industrial outflow.",
            severity: "CRITICAL"
          }] : [],
          global_stats: {
            navi_mumbai_avg_bod: 10.2,
            navi_mumbai_avg_cod: 54.5,
            navi_mumbai_avg_aqi: 165,
            navi_mumbai_total_flow_mld: 980.0,
            active_sensor_nodes: 10,
            telemetry_fps_target: 60.0
          }
        };

        setHistoricalBuffer((b) => {
          const updated = [...b, newPayload];
          if (updated.length > 20) updated.shift();
          return updated;
        });

        return newPayload;
      });
    }, 2000);

    return () => clearInterval(fallbackInterval);
  }, [wsConnected]);

  /**
   * Camera Drill-Down Handler with 60 FPS Interpolation
   */
  const handleSelectFeature = useCallback((feature, level, targetViewState) => {
    setSelectedFeature(feature);
    setDrillDownLevel(level);
    if (targetViewState) {
      setViewState((prev) => ({
        ...prev,
        ...targetViewState
      }));
    }
  }, []);

  /**
   * Breadcrumb Reset Camera Handler
   */
  const handleResetView = useCallback((level) => {
    setDrillDownLevel(level);
    if (level === 'city') {
      setSelectedFeature(NAVI_MUMBAI_WARDS_GEOJSON.features[0]);
    } else if (level === 'state') {
      setSelectedFeature(MAHARASHTRA_DISTRICTS_GEOJSON.features[0]);
    } else {
      setSelectedFeature(null);
    }

    if (PRESET_VIEW_STATES[level]) {
      setViewState((prev) => ({
        ...prev,
        ...PRESET_VIEW_STATES[level]
      }));
    }
  }, []);

  /**
   * Quick Focus on Navi Mumbai (Primary MVP Action)
   */
  const handleFocusNaviMumbai = useCallback(() => {
    handleResetView('city');
  }, [handleResetView]);

  /**
   * Toggle 3D Tilt / Top-Down View
   */
  const handleTogglePitch = useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      pitch: prev.pitch > 10 ? 0 : 55,
      bearing: prev.pitch > 10 ? 0 : 25,
      transitionDuration: 1000,
      transitionInterpolator: new FlyToInterpolator()
    }));
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-cyber-900 select-none">
      {/* Top HUD Navigation */}
      <Navbar
        wsConnected={wsConnected}
        sequence={telemetryData?.sequence || 0}
        timestamp={telemetryData?.timestamp}
        drillDownLevel={drillDownLevel}
        selectedFeature={selectedFeature}
        onResetView={handleResetView}
        metricMode={metricMode}
        setMetricMode={setMetricMode}
        activeAlertCount={telemetryData?.active_alerts?.length || 0}
      />

      {/* Layer Controls & Quick Actions */}
      <LayerControls
        layerOptions={layerOptions}
        setLayerOptions={setLayerOptions}
        onFocusNaviMumbai={handleFocusNaviMumbai}
        onResetPitch={handleTogglePitch}
      />

      {/* Main 60 FPS Hardware-Accelerated WebGL Deck.gl Map */}
      <main className="w-full h-full">
        <MapWrapper
          viewState={viewState}
          onViewStateChange={({ viewState }) => setViewState(viewState)}
          drillDownLevel={drillDownLevel}
          onSelectFeature={handleSelectFeature}
          telemetryData={telemetryData}
          metricMode={metricMode}
          layerOptions={layerOptions}
          selectedFeature={selectedFeature}
        />
      </main>

      {/* Sliding Comparative Analytics Panel (Framer Motion + Recharts) */}
      <AnalyticsPanel
        selectedFeature={selectedFeature}
        onClose={() => setSelectedFeature(null)}
        telemetryData={telemetryData}
        historicalBuffer={historicalBuffer}
      />

      {/* Bottom Real-time Aggregate HUD Bar */}
      <MetricsBar
        globalStats={telemetryData?.global_stats}
        latestAlert={telemetryData?.active_alerts?.[0]}
      />
    </div>
  );
}
