import React, { useState, useEffect } from 'react';
import {
  Battery, AlertTriangle, Sparkles, Gauge, CalendarRange,
  Zap, HeartPulse, LineChart as ChartIcon, CheckCircle2
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { vehicleService, batteryService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const BatteryManagement: React.FC = () => {
  const [vehicle, setVehicle] = useState<any>(null);
  const [healthData, setHealthData] = useState<any>(null);
  const [degradationData, setDegradationData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const vehicles = await vehicleService.getVehicles();
      if (vehicles && vehicles.length > 0) {
        const v = vehicles[0];
        setVehicle(v);
        
        // Fetch health & regression forecasts
        const health = await batteryService.getBatteryHealth(v.id);
        const prediction = await batteryService.getBatteryDegradationPredict(v.id);
        
        setHealthData(health);
        setDegradationData(prediction);
      } else {
        setError('No registered vehicle found. Add one in My EV.');
      }
    } catch (err) {
      setError('Failed to load battery analytics.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        </div>
      </DashboardLayout>
    );
  }

  // Format degradation data for Recharts area comparisons
  const forecastChartData = degradationData?.predicted_curve.map((p: any) => ({
    cycle: p.cycle,
    normal: p.soh_normal,
    abuse: p.soh_abuse
  })) || [];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        
        {/* Header */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Battery Degradation Analytics</h1>
          <p className="text-gray-400 text-sm mt-1">
            Predictive health modeling and SOH degradation profiles under normal vs abuse temperature conditions.
          </p>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        {/* Dynamic health KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Current State of Health (SOH)</p>
              <p className="text-2xl font-black text-white">{healthData?.soh}%</p>
              <span className="text-xs text-emerald-400 font-semibold">{healthData?.health_status}</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-cyan-500/10 rounded-lg text-cyan-400">
              <CalendarRange className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Est. Useful Life Remaining</p>
              <p className="text-2xl font-black text-white">{healthData?.estimated_years_remaining} Years</p>
              <span className="text-xs text-gray-400">{healthData?.predicted_cycles_remaining} cycles left</span>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 rounded-lg text-purple-400">
              <Gauge className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Total Charge Cycles</p>
              <p className="text-2xl font-black text-white">{healthData?.cycle_count}</p>
              <span className="text-xs text-gray-400">Nominal design: 1,500</span>
            </div>
          </div>
        </div>

        {/* Degradation Chart Comparisons */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-2">
              <ChartIcon className="w-5 h-5 text-cyan-400" />
              <h3 className="font-bold text-lg text-white">SOH Degradation Profile (500 Cycle Forecast)</h3>
            </div>
            
            <div className="flex gap-4 text-xs font-semibold text-gray-400">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-400/30 border border-emerald-400"></span> Normal Wear</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-400/30 border border-red-400"></span> Thermal Abuse (42°C)</span>
            </div>
          </div>

          <div className="h-72 w-full">
            {forecastChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastChartData} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34d399" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorAbuse" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f87171" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#f87171" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="cycle" stroke="#64748b" style={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" domain={[70, 100]} style={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <Area type="monotone" dataKey="normal" name="Normal (Temp 25°C)" stroke="#34d399" fillOpacity={1} fill="url(#colorNormal)" strokeWidth={2.5} />
                  <Area type="monotone" dataKey="abuse" name="High Thermal Load (42°C)" stroke="#f87171" fillOpacity={1} fill="url(#colorAbuse)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                No degradation data returned.
              </div>
            )}
          </div>
        </div>

        {/* Explainable model note */}
        <div className="p-4 bg-cyan-500/5 border border-cyan-500/20 text-gray-400 rounded-xl text-xs space-y-2">
          <p className="font-bold text-white uppercase text-[10px] tracking-wider text-cyan-400">Model Methodology:</p>
          <p>
            Battery degradation curves are generated using a physics-informed Gradient Boosting Regressor trained on lithium-ion capacity fade parameters. 
            The curves clearly validate that maintaining a thermal environment below 35°C significantly delays the end-of-life threshold.
          </p>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default BatteryManagement;
