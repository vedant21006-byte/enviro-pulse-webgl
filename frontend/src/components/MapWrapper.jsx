import React, { useState, useMemo, useCallback } from 'react';
import DeckGL from '@deck.gl/react';
import { GeoJsonLayer, ScatterplotLayer, ColumnLayer, TextLayer } from '@deck.gl/layers';
import { FlyToInterpolator } from '@deck.gl/core';
import Map from 'react-map-gl/maplibre'; // Optional if react-map-gl is installed, else DeckGL standalone
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { INDIA_STATES_GEOJSON } from '../data/indiaGeoData';
import { MAHARASHTRA_DISTRICTS_GEOJSON } from '../data/maharashtraGeoData';
import { NAVI_MUMBAI_WARDS_GEOJSON } from '../data/naviMumbaiGeoData';

// Free high-performance dark basemap style using Fastly CDN raster tiles
const CARTO_DARK_STYLE = {
  version: 8,
  sources: {
    'carto-dark': {
      type: 'raster',
      tiles: [
        'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
        'https://cartodb-basemaps-b.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
        'https://cartodb-basemaps-c.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
        'https://cartodb-basemaps-d.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png'
      ],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap &copy; CARTO'
    }
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': '#070b13'
      }
    },
    {
      id: 'carto-dark-tiles',
      type: 'raster',
      source: 'carto-dark',
      minzoom: 0,
      maxzoom: 20
    }
  ]
};

/**
 * 60 FPS Hardware-Accelerated Color Interpolation Helper
 */
function getMetricColor(telemetry, metricMode, alpha = 200) {
  if (!telemetry) return [30, 41, 59, alpha];

  if (metricMode === 'water') {
    const bod = telemetry.bod || 8.0;
    // BOD scale: < 5 good (cyan/emerald), 5-12 moderate (amber), > 12 critical (rose/magenta)
    if (bod < 6.0) return [16, 185, 129, alpha]; // Emerald
    if (bod < 11.0) return [245, 158, 11, alpha]; // Amber
    if (bod < 15.0) return [244, 63, 94, alpha]; // Rose
    return [225, 29, 72, alpha + 30]; // Crimson Critical
  } else if (metricMode === 'air') {
    const aqi = telemetry.aqi || 120;
    // AQI scale: < 100 Good, 100-200 Moderate, > 200 Poor
    if (aqi < 100) return [16, 185, 129, alpha];
    if (aqi < 180) return [245, 158, 11, alpha];
    if (aqi < 240) return [239, 68, 68, alpha];
    return [168, 85, 247, alpha + 30]; // Severe Purple
  } else {
    // Composite Risk Index: Blended BOD + AQI
    const bodScore = Math.min((telemetry.bod || 8.0) / 20.0, 1.0);
    const aqiScore = Math.min((telemetry.aqi || 150) / 300.0, 1.0);
    const risk = (bodScore + aqiScore) / 2.0;

    if (risk < 0.35) return [0, 240, 255, alpha]; // Cyan
    if (risk < 0.65) return [245, 158, 11, alpha]; // Amber
    return [244, 63, 94, alpha + 40]; // High Risk Rose
  }
}

export default function MapWrapper({
  viewState,
  onViewStateChange,
  drillDownLevel,
  onSelectFeature,
  telemetryData,
  metricMode,
  layerOptions,
  selectedFeature
}) {
  const [hoverInfo, setHoverInfo] = useState(null);

  // Extract fast-lookup telemetry tables
  const statesTelemetry = telemetryData?.states || {};
  const districtsTelemetry = telemetryData?.maharashtra_districts || {};
  const wardsTelemetry = telemetryData?.navi_mumbai_wards || {};
  const telemetryTimestamp = telemetryData?.timestamp || 0;

  /**
   * Click Handler for Hierarchical Drill-Down with 60 FPS FlyTo Interpolation
   */
  const handleFeatureClick = useCallback((info) => {
    if (!info.object) return;
    const { object } = info;
    const id = object.id || object.properties?.id;
    const name = object.properties?.name;

    if (drillDownLevel === 'national') {
      if (id === 'IN-MH' || name === 'Maharashtra') {
        // Drill down to Maharashtra
        onSelectFeature(object, 'state', {
          longitude: 75.7139,
          latitude: 19.7515,
          zoom: 6.8,
          pitch: 35,
          bearing: -10,
          transitionDuration: 1800,
          transitionInterpolator: new FlyToInterpolator({ speed: 1.2, curve: 1.4 })
        });
      } else {
        // Center on other states
        const center = object.properties?.center || [info.coordinate[0], info.coordinate[1]];
        onSelectFeature(object, 'national', {
          longitude: center[0],
          latitude: center[1],
          zoom: 5.5,
          pitch: 20,
          bearing: 0,
          transitionDuration: 1500,
          transitionInterpolator: new FlyToInterpolator()
        });
      }
    } else if (drillDownLevel === 'state') {
      if (id === 'MH-NM' || name === 'Navi Mumbai') {
        // Drill down into Navi Mumbai (Primary Focus)
        onSelectFeature(object, 'city', {
          longitude: 73.0297,
          latitude: 19.0330,
          zoom: 12.5,
          pitch: 52,
          bearing: 25,
          transitionDuration: 2000,
          transitionInterpolator: new FlyToInterpolator({ speed: 1.3, curve: 1.5 })
        });
      } else {
        const center = object.properties?.center || [73.0, 19.0];
        onSelectFeature(object, 'state', {
          longitude: center[0],
          latitude: center[1],
          zoom: 11.0,
          pitch: 40,
          bearing: 10,
          transitionDuration: 1600,
          transitionInterpolator: new FlyToInterpolator()
        });
      }
    } else {
      // Drill down to specific Ward in Navi Mumbai
      const center = object.properties?.center || [info.coordinate[0], info.coordinate[1]];
      const zoom = object.properties?.camera_zoom || 14.2;
      const pitch = object.properties?.camera_pitch || 58;
      const bearing = object.properties?.camera_bearing || 30;

      onSelectFeature(object, 'ward', {
        longitude: center[0],
        latitude: center[1],
        zoom: zoom,
        pitch: pitch,
        bearing: bearing,
        transitionDuration: 1600,
        transitionInterpolator: new FlyToInterpolator({ speed: 1.1 })
      });
    }
  }, [drillDownLevel, onSelectFeature]);

  /**
   * Optimized 60 FPS Layer Construction Pipeline
   * Memoized on telemetryTimestamp and view configuration to prevent GC pauses.
   */
  const layers = useMemo(() => {
    const layerList = [];

    // -------------------------------------------------------------------------
    // 1. NATIONAL LEVEL: India States Base GeoJSON Layer
    // -------------------------------------------------------------------------
    if (drillDownLevel === 'national') {
      layerList.push(
        new GeoJsonLayer({
          id: 'india-states-layer',
          data: INDIA_STATES_GEOJSON,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: false,
          lineWidthMinPixels: 1.5,
          getLineColor: (f) => f.properties.primary_focus ? [0, 240, 255, 255] : [56, 189, 248, 120],
          getFillColor: (f) => {
            const telemetry = statesTelemetry[f.properties.id];
            return getMetricColor(telemetry, metricMode, f.properties.primary_focus ? 140 : 80);
          },
          updateTriggers: {
            getFillColor: [telemetryTimestamp, metricMode],
            getLineColor: [drillDownLevel]
          },
          transitions: {
            getFillColor: 400
          },
          onClick: handleFeatureClick,
          onHover: (info) => setHoverInfo(info)
        })
      );
    }

    // -------------------------------------------------------------------------
    // 2. STATE LEVEL: Maharashtra Districts Layer
    // -------------------------------------------------------------------------
    if (drillDownLevel === 'state' || drillDownLevel === 'national') {
      layerList.push(
        new GeoJsonLayer({
          id: 'maharashtra-districts-layer',
          data: MAHARASHTRA_DISTRICTS_GEOJSON,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: true,
          wireframe: layerOptions.showWireframes,
          lineWidthMinPixels: 2,
          getElevation: (f) => {
            const telemetry = districtsTelemetry[f.properties.id];
            if (!telemetry || !layerOptions.show3dColumns) return 0;
            return (telemetry.cod || 40) * 120; // 3D Extrusion proportional to COD
          },
          getLineColor: (f) => f.properties.primary_focus ? [0, 240, 255, 255] : [100, 116, 139, 180],
          getFillColor: (f) => {
            const telemetry = districtsTelemetry[f.properties.id];
            const isSelected = selectedFeature?.properties?.id === f.properties.id;
            const alpha = isSelected ? 220 : f.properties.primary_focus ? 170 : 100;
            return getMetricColor(telemetry, metricMode, alpha);
          },
          updateTriggers: {
            getFillColor: [telemetryTimestamp, metricMode, selectedFeature],
            getElevation: [telemetryTimestamp, layerOptions.show3dColumns]
          },
          transitions: {
            getFillColor: 400,
            getElevation: 500
          },
          onClick: handleFeatureClick,
          onHover: (info) => setHoverInfo(info)
        })
      );
    }

    // -------------------------------------------------------------------------
    // 3. CITY & WARD LEVEL: Navi Mumbai Wards & Volumetric Sensor Extrusions
    // -------------------------------------------------------------------------
    if (drillDownLevel === 'city' || drillDownLevel === 'ward') {
      // 3A. Base Ward Polygons
      layerList.push(
        new GeoJsonLayer({
          id: 'navi-mumbai-wards-layer',
          data: NAVI_MUMBAI_WARDS_GEOJSON,
          pickable: true,
          stroked: true,
          filled: true,
          extruded: false,
          lineWidthMinPixels: 2,
          getLineColor: (f) => {
            const isSelected = selectedFeature?.properties?.id === f.properties.id;
            return isSelected ? [0, 240, 255, 255] : [56, 189, 248, 140];
          },
          getFillColor: (f) => {
            const telemetry = wardsTelemetry[f.properties.id];
            const isSelected = selectedFeature?.properties?.id === f.properties.id;
            const alpha = isSelected ? 220 : 130;
            return getMetricColor(telemetry, metricMode, alpha);
          },
          updateTriggers: {
            getFillColor: [telemetryTimestamp, metricMode, selectedFeature],
            getLineColor: [selectedFeature]
          },
          transitions: {
            getFillColor: 400
          },
          onClick: handleFeatureClick,
          onHover: (info) => setHoverInfo(info)
        })
      );

      // 3B. 3D Volumetric Columns for Pollutant Footprint (COD/BOD)
      if (layerOptions.show3dColumns) {
        const columnData = NAVI_MUMBAI_WARDS_GEOJSON.features.map(f => {
          const telemetry = wardsTelemetry[f.properties.id];
          return {
            id: f.properties.id,
            name: f.properties.name,
            coordinates: f.properties.center,
            elevation: (telemetry?.cod || 30) * 45, // Proportional height in meters
            telemetry: telemetry
          };
        });

        layerList.push(
          new ColumnLayer({
            id: 'navi-mumbai-3d-columns',
            data: columnData,
            diskResolution: 24,
            radius: 380,
            extruded: true,
            pickable: true,
            elevationScale: 1,
            getPosition: (d) => d.coordinates,
            getElevation: (d) => d.elevation,
            getFillColor: (d) => getMetricColor(d.telemetry, metricMode, 190),
            getLineColor: [0, 240, 255, 255],
            lineWidthMinPixels: 1.5,
            updateTriggers: {
              getElevation: [telemetryTimestamp],
              getFillColor: [telemetryTimestamp, metricMode]
            },
            transitions: {
              getElevation: 600,
              getFillColor: 400
            },
            onClick: handleFeatureClick,
            onHover: (info) => setHoverInfo(info)
          })
        );
      }

      // 3C. Pulsating Sensor Node Beacons
      if (layerOptions.showSensorNodes) {
        const beaconData = NAVI_MUMBAI_WARDS_GEOJSON.features.map(f => ({
          id: f.properties.id,
          name: f.properties.name,
          coordinates: f.properties.center,
          sensor_id: f.properties.sensor_id,
          telemetry: wardsTelemetry[f.properties.id]
        }));

        layerList.push(
          new ScatterplotLayer({
            id: 'navi-mumbai-sensor-beacons',
            data: beaconData,
            getPosition: (d) => d.coordinates,
            getRadius: 280,
            radiusMinPixels: 6,
            radiusMaxPixels: 24,
            getFillColor: (d) => getMetricColor(d.telemetry, metricMode, 255),
            getLineColor: [255, 255, 255, 255],
            lineWidthMinPixels: 2,
            stroked: true,
            filled: true,
            pickable: true,
            updateTriggers: {
              getFillColor: [telemetryTimestamp, metricMode]
            },
            transitions: {
              getRadius: 300,
              getFillColor: 400
            },
            onClick: handleFeatureClick,
            onHover: (info) => setHoverInfo(info)
          })
        );

        // 3D Text Labels on top of Sensor Beacons
        layerList.push(
          new TextLayer({
            id: 'navi-mumbai-ward-labels',
            data: beaconData,
            getPosition: (d) => [d.coordinates[0], d.coordinates[1], (d.telemetry?.cod || 30) * 45 + 50],
            getText: (d) => d.name.split(' ')[0],
            getSize: 12,
            getColor: [255, 255, 255, 230],
            getAngle: 0,
            getTextAnchor: 'middle',
            getAlignmentBaseline: 'center',
            backgroundColor: [7, 11, 19, 180],
            backgroundPadding: [4, 2],
            fontFamily: 'JetBrains Mono, monospace',
            updateTriggers: {
              getPosition: [telemetryTimestamp]
            }
          })
        );
      }
    }

    return layerList;
  }, [
    drillDownLevel,
    statesTelemetry,
    districtsTelemetry,
    wardsTelemetry,
    telemetryTimestamp,
    metricMode,
    layerOptions,
    selectedFeature,
    handleFeatureClick
  ]);

  /**
   * Rich 60 FPS Tooltip Renderer
   */
  const renderTooltip = () => {
    if (!hoverInfo || !hoverInfo.object) return null;
    const { object, x, y } = hoverInfo;
    const id = object.id || object.properties?.id;
    const name = object.name || object.properties?.name || "Region";
    const type = object.properties?.type || "Environmental Node";
    
    // Look up live telemetry
    const telemetry = wardsTelemetry[id] || districtsTelemetry[id] || statesTelemetry[id] || object.telemetry;

    return (
      <div 
        className="deck-tooltip"
        style={{ left: x + 15, top: y + 15 }}
      >
        <div className="flex items-center justify-between gap-3 border-b border-slate-700/80 pb-1 mb-1.5">
          <strong className="text-cyan-300 font-bold">{name}</strong>
          <span className="text-[10px] font-mono px-1.5 py-0.2 bg-cyan-950 border border-cyan-500/40 text-cyan-300 rounded">
            {id}
          </span>
        </div>
        <p className="text-[10px] text-slate-400 mb-2">{type}</p>

        {telemetry ? (
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-400">BOD:</span>
              <span className="text-cyan-300 font-bold">{telemetry.bod} mg/L</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">COD:</span>
              <span className="text-indigo-300 font-bold">{telemetry.cod} mg/L</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">AQI:</span>
              <span className="text-amber-300 font-bold">{telemetry.aqi}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">DO:</span>
              <span className="text-emerald-300 font-bold">{telemetry.do} mg/L</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">PM2.5:</span>
              <span className="text-rose-300 font-bold">{telemetry.pm25} µg/m³</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Flow:</span>
              <span className="text-teal-300 font-bold">{telemetry.water_flow_mld} MLD</span>
            </div>
          </div>
        ) : (
          <div className="text-[11px] text-slate-400 italic">Click to drill down</div>
        )}
      </div>
    );
  };

  return (
    <div className="relative w-full h-full">
      <DeckGL
        viewState={viewState}
        onViewStateChange={onViewStateChange}
        controller={{
          doubleClickZoom: false,
          touchRotate: true,
          dragRotate: true,
          inertia: true
        }}
        layers={layers}
        mapLib={maplibregl}
        mapStyle={CARTO_DARK_STYLE}
        getCursor={({ isHovering }) => (isHovering ? 'pointer' : 'default')}
      />
      {renderTooltip()}
    </div>
  );
}
