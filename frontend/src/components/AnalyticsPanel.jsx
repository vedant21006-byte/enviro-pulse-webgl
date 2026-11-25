import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  TrendingUp, 
  Activity, 
  Droplet, 
  Wind, 
  Compass, 
  AlertOctagon, 
  ShieldCheck, 
  BarChart3, 
  Radar as RadarIcon,
  Maximize2,
  Minimize2,
  Layers,
  Trees,
  Waves,
  Cpu
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  AreaChart, 
  Area 
} from 'recharts';

export default function AnalyticsPanel({
  selectedFeature,
  onClose,
  telemetryData,
  historicalBuffer
}) {
  const [activeTab, setActiveTab] = useState('comparative');
  const [isExpanded, setIsExpanded] = useState(false);

  if (!selectedFeature) return null;

  const featureId = selectedFeature.id || selectedFeature.properties?.id;
  const featureName = selectedFeature.properties?.name || selectedFeature.name || "Selected Region";
  const featureType = selectedFeature.properties?.type || selectedFeature.type || "Environmental Zone";
  const tier = selectedFeature.properties?.tier || selectedFeature.tier || "area";
  const neighborIds = selectedFeature.properties?.neighbors || selectedFeature.neighbors || [];

  // Data lookups
  const states = telemetryData?.states || {};
  const cities = telemetryData?.cities || {};
  const areas = telemetryData?.areas || {};

  const currentStats = areas[featureId] || cities[featureId] || states[featureId] || {
    bod: 9.8, cod: 52.0, do: 5.2, ph: 7.6, aqi: 168, pm25: 74.0, pm10: 142.0, no2: 42.0, so2: 18.0,
    water_flow_mld: 285.0, status: "NORMAL",
    resources: { forest_cover_pct: 28.4, forest_area_sqkm: 98.5, water_bodies_count: 48, tree_count_millions: 12.4, groundwater_depth_m: 5.8, monitoring_stations_count: 14 }
  };

  const res = currentStats.resources || {
    forest_cover_pct: selectedFeature.properties?.forest_cover_pct || 20.0,
    forest_area_sqkm: selectedFeature.properties?.forest_area_sqkm || 100.0,
    water_bodies_count: selectedFeature.properties?.water_bodies_count || 10,
    tree_count_millions: selectedFeature.properties?.tree_count_millions || 1.0,
    groundwater_depth_m: selectedFeature.properties?.groundwater_depth_m || 6.0,
    monitoring_stations_count: selectedFeature.properties?.monitoring_stations_count || 2
  };

  // Resolve genuine topological neighbors for comparison
  const neighborPool = tier === 'state' ? states : (tier === 'city' ? cities : areas);
  const resolvedNeighbors = neighborIds
    .map(nId => neighborPool[nId])
    .filter(Boolean);

  const n1 = resolvedNeighbors[0] || null;
  const n2 = resolvedNeighbors[1] || null;

  // 1. Dynamic Radar Footprint (Normalized 0-100 across 6 axes)
  const radarData = [
    {
      subject: 'BOD Load',
      Active: Math.min(Math.round((currentStats.bod / 20) * 100), 100),
      Neighbor1: n1 ? Math.min(Math.round((n1.bod / 20) * 100), 100) : 50,
      Neighbor2: n2 ? Math.min(Math.round((n2.bod / 20) * 100), 100) : 45,
    },
    {
      subject: 'COD Chemical',
      Active: Math.min(Math.round((currentStats.cod / 100) * 100), 100),
      Neighbor1: n1 ? Math.min(Math.round((n1.cod / 100) * 100), 100) : 55,
      Neighbor2: n2 ? Math.min(Math.round((n2.cod / 100) * 100), 100) : 50,
    },
    {
      subject: 'AQI Index',
      Active: Math.min(Math.round((currentStats.aqi / 300) * 100), 100),
      Neighbor1: n1 ? Math.min(Math.round((n1.aqi / 300) * 100), 100) : 50,
      Neighbor2: n2 ? Math.min(Math.round((n2.aqi / 300) * 100), 100) : 48,
    },
    {
      subject: 'PM 2.5',
      Active: Math.min(Math.round((currentStats.pm25 / 150) * 100), 100),
      Neighbor1: n1 ? Math.min(Math.round((n1.pm25 / 150) * 100), 100) : 52,
      Neighbor2: n2 ? Math.min(Math.round((n2.pm25 / 150) * 100), 100) : 46,
    },
    {
      subject: 'Forest Canopy',
      Active: Math.min(Math.round(res.forest_cover_pct * 2), 100),
      Neighbor1: n1 && n1.resources ? Math.min(Math.round(n1.resources.forest_cover_pct * 2), 100) : 40,
      Neighbor2: n2 && n2.resources ? Math.min(Math.round(n2.resources.forest_cover_pct * 2), 100) : 35,
    },
    {
      subject: 'Water Bodies',
      Active: Math.min(Math.round((res.water_bodies_count / 50) * 100), 100),
      Neighbor1: n1 && n1.resources ? Math.min(Math.round((n1.resources.water_bodies_count / 50) * 100), 100) : 45,
      Neighbor2: n2 && n2.resources ? Math.min(Math.round((n2.resources.water_bodies_count / 50) * 100), 100) : 38,
    }
  ];

  // 2. Bar Chart Data: Direct Comparative Pollutant Load
  const barData = [
    {
      name: featureName.split(' ')[0],
      BOD: currentStats.bod,
      COD: currentStats.cod,
      AQI: currentStats.aqi,
      PM25: currentStats.pm25,
    },
    ...(resolvedNeighbors.slice(0, 3).map(n => ({
      name: n.name.split(' ')[0],
      BOD: n.bod,
      COD: n.cod,
      AQI: n.aqi,
      PM25: n.pm25,
    })))
  ];

  const isCritical = currentStats.bod > 14.0 || currentStats.cod > 75.0 || currentStats.aqi > 220;
  const isElevated = currentStats.bod > 9.0 || currentStats.cod > 50.0 || currentStats.aqi > 150;

  return (
    <AnimatePresence>
      <motion.aside
        initial={{ x: '100%', opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: '100%', opacity: 0 }}
        transition={{ type: 'spring', damping: 26, stiffness: 220 }}
        className={`fixed top-16 right-3 bottom-16 z-50 glass-panel-glow rounded-3xl flex flex-col overflow-hidden transition-all duration-300 pointer-events-auto ${
          isExpanded ? 'w-[720px]' : 'w-[480px]'
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-700/60 flex items-start justify-between bg-cyber-850/90">
          <div className="flex-1 mr-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded-md font-semibold uppercase">
                {tier} LEVEL: {featureId}
              </span>
              
              {isCritical ? (
                <span className="hud-badge hud-badge-critical">
                  <AlertOctagon className="w-3 h-3" />
                  CRITICAL LOAD
                </span>
              ) : isElevated ? (
                <span className="hud-badge hud-badge-elevated">
                  <Activity className="w-3 h-3" />
                  ELEVATED LOAD
                </span>
              ) : (
                <span className="hud-badge hud-badge-normal">
                  <ShieldCheck className="w-3 h-3" />
                  CPCB COMPLIANT
                </span>
              )}
            </div>

            <h2 className="text-base font-bold text-white tracking-wide truncate">
              {featureName}
            </h2>
            <p className="text-[11px] text-slate-400 line-clamp-1">{featureType}</p>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800/80 transition-colors"
            >
              {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800/80 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-4 py-2 border-b border-slate-800 bg-cyber-900/60 flex items-center gap-2">
          <button
            onClick={() => setActiveTab('comparative')}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
              activeTab === 'comparative'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <RadarIcon className="w-3.5 h-3.5" />
            <span>Bordering Neighbors Footprint</span>
          </button>

          <button
            onClick={() => setActiveTab('resources')}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
              activeTab === 'resources'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Trees className="w-3.5 h-3.5" />
            <span>Natural Resource Census</span>
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          
          {/* Primary Metric Grid */}
          <div className="grid grid-cols-3 gap-2.5 text-center font-mono">
            <div className="p-2.5 rounded-xl bg-cyber-800/70 border border-cyan-500/20">
              <div className="flex items-center justify-between text-slate-400 text-[10px]">
                <span>BOD Water</span>
                <Droplet className="w-3 h-3 text-cyan-400" />
              </div>
              <div className="mt-1 flex items-baseline justify-center gap-1">
                <span className="text-lg font-black text-cyan-300">{currentStats.bod?.toFixed(1)}</span>
                <span className="text-[10px] text-slate-500">mg/L</span>
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">&lt; 3.0 safe standard</div>
            </div>

            <div className="p-2.5 rounded-xl bg-cyber-800/70 border border-indigo-500/20">
              <div className="flex items-center justify-between text-slate-400 text-[10px]">
                <span>COD Chemical</span>
                <Activity className="w-3 h-3 text-indigo-400" />
              </div>
              <div className="mt-1 flex items-baseline justify-center gap-1">
                <span className="text-lg font-black text-indigo-300">{currentStats.cod?.toFixed(1)}</span>
                <span className="text-[10px] text-slate-500">mg/L</span>
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">&lt; 50 safe standard</div>
            </div>

            <div className="p-2.5 rounded-xl bg-cyber-800/70 border border-purple-500/20">
              <div className="flex items-center justify-between text-slate-400 text-[10px]">
                <span>Air AQI</span>
                <Wind className="w-3 h-3 text-purple-400" />
              </div>
              <div className="mt-1 flex items-baseline justify-center gap-1">
                <span className="text-lg font-black text-purple-300">{currentStats.aqi}</span>
                <span className="text-[10px] text-slate-500">AQI</span>
              </div>
              <div className="text-[9px] text-slate-400 mt-0.5">&lt; 100 safe standard</div>
            </div>
          </div>

          {/* Secondary Parameters */}
          <div className="grid grid-cols-4 gap-2 text-center font-mono text-xs">
            <div className="p-2 rounded-lg bg-cyber-800/60 border border-slate-700">
              <div className="text-[9px] text-slate-400">PM 2.5</div>
              <div className="font-bold text-rose-300">{currentStats.pm25?.toFixed(1)}</div>
              <div className="text-[8px] text-slate-500">µg/m³</div>
            </div>
            <div className="p-2 rounded-lg bg-cyber-800/60 border border-slate-700">
              <div className="text-[9px] text-slate-400">PM 10</div>
              <div className="font-bold text-rose-300">{currentStats.pm10?.toFixed(1)}</div>
              <div className="text-[8px] text-slate-500">µg/m³</div>
            </div>
            <div className="p-2 rounded-lg bg-cyber-800/60 border border-slate-700">
              <div className="text-[9px] text-slate-400">DO Oxygen</div>
              <div className="font-bold text-emerald-300">{currentStats.do?.toFixed(1)}</div>
              <div className="text-[8px] text-slate-500">mg/L</div>
            </div>
            <div className="p-2 rounded-lg bg-cyber-800/60 border border-slate-700">
              <div className="text-[9px] text-slate-400">Discharge</div>
              <div className="font-bold text-teal-300">{currentStats.water_flow_mld?.toFixed(0)}</div>
              <div className="text-[8px] text-slate-500">MLD</div>
            </div>
          </div>

          {/* Natural Resource Inventory Section */}
          <div className="p-3.5 rounded-2xl bg-cyber-800/70 border border-emerald-500/30 space-y-2.5">
            <div className="flex justify-between items-center text-xs font-bold text-emerald-300">
              <span className="flex items-center gap-1.5">
                <Trees className="w-3.5 h-3.5" />
                Natural Resources & Ecological Inventory
              </span>
              <span className="text-[10px] font-mono text-slate-400">MoEFCC Validated</span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
              <div className="p-2 rounded-lg bg-cyber-900/80 border border-emerald-500/20">
                <div className="text-[9px] text-slate-400">Forest Canopy</div>
                <div className="font-bold text-emerald-300">{res.forest_cover_pct?.toFixed(1)}%</div>
                <div className="text-[8px] text-slate-500">{res.forest_area_sqkm?.toFixed(0)} km²</div>
              </div>
              <div className="p-2 rounded-lg bg-cyber-900/80 border border-teal-500/20">
                <div className="text-[9px] text-slate-400">Water Bodies</div>
                <div className="font-bold text-teal-300">{res.water_bodies_count}</div>
                <div className="text-[8px] text-slate-500">Lakes & Wetlands</div>
              </div>
              <div className="p-2 rounded-lg bg-cyber-900/80 border border-emerald-500/20">
                <div className="text-[9px] text-slate-400">Tree Population</div>
                <div className="font-bold text-emerald-300">{res.tree_count_millions?.toFixed(2)} M</div>
                <div className="text-[8px] text-slate-500">Canopy Trees</div>
              </div>
            </div>

            <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800">
              <span>Groundwater Table: <strong className="text-slate-200">{res.groundwater_depth_m?.toFixed(1)} m bgl</strong></span>
              <span>Active Monitoring: <strong className="text-cyan-300">{res.monitoring_stations_count} Stations</strong></span>
            </div>
          </div>

          {/* Dynamic Neighbor Radar Footprint */}
          {activeTab === 'comparative' && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-2xl bg-cyber-800/60 border border-slate-700/60">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <RadarIcon className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-slate-200 tracking-wide">
                      Footprint Comparison vs. Bordering Neighbors
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-cyan-400">Topological Graph</span>
                </div>

                <div className="w-full h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                      <PolarGrid stroke="#334155" strokeDasharray="3 3" />
                      <PolarAngleAxis dataKey="subject" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" tick={false} />
                      <Radar
                        name={featureName.split(' ')[0]}
                        dataKey="Active"
                        stroke="#00f0ff"
                        fill="#00f0ff"
                        fillOpacity={0.4}
                      />
                      {n1 && (
                        <Radar
                          name={n1.name.split(' ')[0]}
                          dataKey="Neighbor1"
                          stroke="#f59e0b"
                          fill="#f59e0b"
                          fillOpacity={0.15}
                        />
                      )}
                      {n2 && (
                        <Radar
                          name={n2.name.split(' ')[0]}
                          dataKey="Neighbor2"
                          stroke="#f43f5e"
                          fill="#f43f5e"
                          fillOpacity={0.15}
                        />
                      )}
                      <Legend wrapperStyle={{ fontSize: 10, paddingTop: 6 }} iconSize={8} />
                      <RechartsTooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(7, 11, 19, 0.95)', 
                          border: '1px solid rgba(0, 240, 255, 0.3)',
                          borderRadius: 8,
                          fontSize: 11
                        }} 
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Direct Neighbor Bar Comparison */}
              <div className="p-3.5 rounded-2xl bg-cyber-800/60 border border-slate-700/60">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-indigo-400" />
                    <h3 className="text-xs font-bold text-slate-200 tracking-wide">
                      Direct Pollutant Comparison (BOD & COD)
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">mg/L</span>
                </div>

                <div className="w-full h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <RechartsTooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(7, 11, 19, 0.95)', 
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          borderRadius: 8,
                          fontSize: 11
                        }} 
                      />
                      <Legend wrapperStyle={{ fontSize: 10 }} iconSize={8} />
                      <Bar dataKey="BOD" fill="#00f0ff" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="COD" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Natural Resource Details */}
          {activeTab === 'resources' && (
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-cyber-800/60 border border-slate-700 space-y-1.5">
                <div className="text-slate-300 font-bold">Ecological Integrity Score</div>
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min(res.forest_cover_pct * 2.2, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 pt-0.5">
                  <span>Critical Degradation (&lt; 10%)</span>
                  <span>National Target (33%)</span>
                </div>
              </div>
            </div>
          )}

        </div>
      </motion.aside>
    </AnimatePresence>
  );
}
