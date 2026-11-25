import React from 'react';
import { Box, Eye, Layers, Compass, Crosshair, Sparkles } from 'lucide-react';

export default function LayerControls({
  layerOptions,
  setLayerOptions,
  onFocusNaviMumbai,
  onResetPitch
}) {
  const toggleOption = (key) => {
    setLayerOptions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className="fixed top-20 left-3 z-40 flex flex-col gap-2 pointer-events-auto">
      <div className="glass-panel p-2 rounded-2xl flex flex-col gap-1.5 shadow-glass">
        <div className="text-[10px] font-mono text-slate-400 px-2 py-1 uppercase tracking-wider border-b border-slate-800 flex items-center justify-between">
          <span>GPU Layers</span>
          <Layers className="w-3 h-3 text-cyan-400" />
        </div>

        {/* 3D Extrusion Toggle */}
        <button
          onClick={() => toggleOption('show3dColumns')}
          className={`hud-btn justify-between ${layerOptions.show3dColumns ? 'hud-btn-active' : ''}`}
        >
          <div className="flex items-center gap-2">
            <Box className="w-3.5 h-3.5" />
            <span>3D Volumetric</span>
          </div>
          <span className={`w-2 h-2 rounded-full ${layerOptions.show3dColumns ? 'bg-cyan-400' : 'bg-slate-600'}`} />
        </button>

        {/* Sensor Beacons */}
        <button
          onClick={() => toggleOption('showSensorNodes')}
          className={`hud-btn justify-between ${layerOptions.showSensorNodes ? 'hud-btn-active' : ''}`}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Sensor Beacons</span>
          </div>
          <span className={`w-2 h-2 rounded-full ${layerOptions.showSensorNodes ? 'bg-cyan-400' : 'bg-slate-600'}`} />
        </button>

        {/* Wireframes */}
        <button
          onClick={() => toggleOption('showWireframes')}
          className={`hud-btn justify-between ${layerOptions.showWireframes ? 'hud-btn-active' : ''}`}
        >
          <div className="flex items-center gap-2">
            <Eye className="w-3.5 h-3.5" />
            <span>Grid Wireframes</span>
          </div>
          <span className={`w-2 h-2 rounded-full ${layerOptions.showWireframes ? 'bg-cyan-400' : 'bg-slate-600'}`} />
        </button>

        <div className="h-px bg-slate-800 my-1" />

        {/* Quick Jump to Navi Mumbai (Primary Hackathon Action) */}
        <button
          onClick={onFocusNaviMumbai}
          className="px-3 py-2 rounded-lg font-mono text-xs font-bold bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 hover:from-cyan-500/30 hover:to-indigo-500/30 border border-cyan-500/40 text-cyan-300 hover:text-white flex items-center justify-between transition-all"
          title="Fly camera directly to Navi Mumbai MVP demonstration zone"
        >
          <div className="flex items-center gap-2">
            <Crosshair className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
            <span>Navi Mumbai Core</span>
          </div>
          <span className="text-[10px] px-1 py-0.2 bg-cyan-400/20 rounded text-cyan-300">MVP</span>
        </button>

        {/* Reset Camera Pitch */}
        <button
          onClick={onResetPitch}
          className="hud-btn justify-center text-slate-400 hover:text-slate-200"
          title="Reset Camera Pitch to 2D Top View"
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Toggle 3D Tilt</span>
        </button>
      </div>
    </div>
  );
}
