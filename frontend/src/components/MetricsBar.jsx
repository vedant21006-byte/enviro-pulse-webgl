import React from 'react';
import { Activity, Droplet, Wind, Gauge, Cpu, AlertTriangle } from 'lucide-react';

export default function MetricsBar({ globalStats, latestAlert }) {
  const avgBod = globalStats?.navi_mumbai_avg_bod ?? 9.8;
  const avgCod = globalStats?.navi_mumbai_avg_cod ?? 52.0;
  const avgAqi = globalStats?.navi_mumbai_avg_aqi ?? 168;
  const totalFlow = globalStats?.navi_mumbai_total_flow_mld ?? 980.0;
  const activeNodes = globalStats?.active_sensor_nodes ?? 29;

  // Determine health color badge
  const getBodColor = (val) => val > 12 ? 'text-rose-400' : val > 8 ? 'text-amber-400' : 'text-emerald-400';
  const getCodColor = (val) => val > 65 ? 'text-rose-400' : val > 45 ? 'text-amber-400' : 'text-emerald-400';
  const getAqiColor = (val) => val > 200 ? 'text-rose-400' : val > 120 ? 'text-amber-400' : 'text-emerald-400';

  return (
    <div className="fixed bottom-3 left-3 z-40 flex items-center gap-3 pointer-events-none">
      {/* Real-Time HUD Metrics Strip */}
      <div className="glass-panel px-4 py-2.5 rounded-2xl flex items-center gap-6 pointer-events-auto">
        
        {/* BOD Metric */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Droplet className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Navi Mumbai BOD</div>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-base font-extrabold font-mono ${getBodColor(avgBod)}`}>
                {avgBod.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">mg/L</span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800" />

        {/* COD Metric */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Navi Mumbai COD</div>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-base font-extrabold font-mono ${getCodColor(avgCod)}`}>
                {avgCod.toFixed(1)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">mg/L</span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800" />

        {/* AQI Metric */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Wind className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Avg Air AQI</div>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-base font-extrabold font-mono ${getAqiColor(avgAqi)}`}>
                {avgAqi.toFixed(0)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">AQI</span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800" />

        {/* Total Water Flow */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
            <Gauge className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">Discharge Flow</div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-base font-extrabold font-mono text-teal-300">
                {totalFlow.toFixed(0)}
              </span>
              <span className="text-[10px] text-slate-500 font-mono">MLD</span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800" />

        {/* GPU Performance Engine */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-mono">GPU Engine</div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-base font-extrabold font-mono text-emerald-400">
                60 FPS
              </span>
              <span className="text-[10px] text-slate-500 font-mono">{activeNodes} Nodes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Ticker for latest alert if present */}
      {latestAlert && (
        <div className="glass-panel px-3 py-2 rounded-2xl flex items-center gap-2 max-w-sm pointer-events-auto border-rose-500/40 bg-rose-950/40 animate-pulse">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <p className="text-[11px] text-rose-200 truncate font-mono">
            <strong className="text-rose-400">{latestAlert.region_name}:</strong> {latestAlert.message}
          </p>
        </div>
      )}
    </div>
  );
}
