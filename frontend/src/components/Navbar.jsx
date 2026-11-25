import React from 'react';
import { 
  Activity, 
  Layers, 
  MapPin, 
  Radio, 
  ShieldAlert, 
  Wifi, 
  WifiOff, 
  ChevronRight,
  Droplets,
  Wind,
  Cpu
} from 'lucide-react';

export default function Navbar({
  wsConnected,
  sequence,
  timestamp,
  drillDownLevel,
  selectedFeature,
  onResetView,
  metricMode,
  setMetricMode,
  activeAlertCount
}) {
  const formattedTime = timestamp 
    ? new Date(timestamp * 1000).toLocaleTimeString('en-US', { hour12: false }) 
    : '--:--:--';

  return (
    <header className="fixed top-3 left-3 right-3 z-50 flex items-center justify-between pointer-events-none">
      {/* Brand & Breadcrumbs */}
      <div className="flex items-center gap-3 pointer-events-auto">
        <div className="glass-panel-glow px-4 py-2 rounded-xl flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center text-cyan-400">
            <Cpu className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-sm tracking-wider text-white bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
                ENVIROPULSE 3D
              </span>
              <span className="px-1.5 py-0.2 bg-cyan-500/10 border border-cyan-500/30 text-[10px] font-mono text-cyan-300 rounded">
                60 FPS WebGL
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              India • Maharashtra • Navi Mumbai Sensor Grid
            </p>
          </div>
        </div>

        {/* Drill-down Breadcrumb Navigator */}
        <nav aria-label="Drill-down Hierarchy" className="glass-panel px-3 py-2 rounded-xl flex items-center gap-2 text-xs font-mono">
          <button 
            onClick={() => onResetView('national')}
            className={`transition-colors ${drillDownLevel === 'national' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            India
          </button>
          
          <ChevronRight className="w-3 h-3 text-slate-600" />
          
          <button 
            onClick={() => onResetView('state')}
            className={`transition-colors ${drillDownLevel === 'state' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Maharashtra
          </button>
          
          <ChevronRight className="w-3 h-3 text-slate-600" />
          
          <button 
            onClick={() => onResetView('city')}
            className={`transition-colors ${drillDownLevel === 'city' ? 'text-cyan-400 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Navi Mumbai
          </button>

          {selectedFeature && drillDownLevel === 'ward' && (
            <>
              <ChevronRight className="w-3 h-3 text-slate-600" />
              <span className="text-emerald-400 font-bold truncate max-w-[120px]">
                {selectedFeature.properties.name.split(' ')[0]}
              </span>
            </>
          )}
        </nav>
      </div>

      {/* Metric Mode Toggle & Stream Telemetry Status */}
      <div className="flex items-center gap-3 pointer-events-auto">
        {/* Metric Selector */}
        <div className="glass-panel p-1 rounded-xl flex items-center gap-1">
          <button
            onClick={() => setMetricMode('water')}
            className={`hud-btn ${metricMode === 'water' ? 'hud-btn-active' : ''}`}
            title="Focus on Water Quality (BOD, COD, Dissolved Oxygen)"
          >
            <Droplets className="w-3.5 h-3.5 text-cyan-400" />
            <span>Water (BOD/COD)</span>
          </button>

          <button
            onClick={() => setMetricMode('air')}
            className={`hud-btn ${metricMode === 'air' ? 'hud-btn-active' : ''}`}
            title="Focus on Air Quality (AQI, PM2.5, PM10)"
          >
            <Wind className="w-3.5 h-3.5 text-purple-400" />
            <span>Air (AQI/PM)</span>
          </button>

          <button
            onClick={() => setMetricMode('composite')}
            className={`hud-btn ${metricMode === 'composite' ? 'hud-btn-active' : ''}`}
            title="Composite Environmental Risk Index"
          >
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>Composite</span>
          </button>
        </div>

        {/* Live WebSocket Status & Clocks */}
        <div className="glass-panel px-3.5 py-2 rounded-xl flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            {wsConnected ? (
              <span className="flex items-center gap-1.5 text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>LIVE 2s</span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-amber-400">
                <Radio className="w-3 h-3 animate-spin" />
                <span>SYNCING</span>
              </span>
            )}
          </div>

          <div className="h-3 w-px bg-slate-700" />

          <div className="text-slate-400">
            SEQ: <span className="text-slate-200">#{sequence}</span>
          </div>

          <div className="h-3 w-px bg-slate-700" />

          <div className="text-cyan-300">
            {formattedTime}
          </div>

          {activeAlertCount > 0 && (
            <>
              <div className="h-3 w-px bg-slate-700" />
              <div className="flex items-center gap-1 text-rose-400 font-bold animate-pulse">
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>{activeAlertCount} ALERTS</span>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
