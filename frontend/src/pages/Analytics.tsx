import React, { useState, useEffect } from 'react';
import { BarChart3, Activity, Zap, Coins, Clock } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { analyticsService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const Analytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await analyticsService.getDashboardAnalytics();
      setAnalytics(data);
    } catch (err) {
      setError('Failed to query station analytics.');
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

  const weeklyEnergy = analytics?.charts?.weekly_energy || [];
  const stationUtil = analytics?.charts?.utilization || [];
  const peakHours = analytics?.charts?.peak_hours || [];
  const summary = analytics?.summary || {};

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Microgrid Analytics</h1>
          <p className="text-gray-400 text-sm mt-1">Deep analytics on station utilization, peak loads, and energy consumption metrics.</p>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        {/* Analytics KPIs grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="glass-panel p-4 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-cyan-500/10 rounded-lg text-cyan-400">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Total Energy Consumed</p>
              <p className="text-lg font-black text-white">{summary.total_energy_kwh} kWh</p>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
              <Coins className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Total Charging Cost</p>
              <p className="text-lg font-black text-white">₹{summary.total_cost_inr}</p>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-purple-500/10 rounded-lg text-purple-400">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Total Sessions</p>
              <p className="text-lg font-black text-white">{summary.total_sessions}</p>
            </div>
          </div>

          <div className="glass-panel p-4 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-amber-500/10 rounded-lg text-amber-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-semibold uppercase">Average Wait Time</p>
              <p className="text-lg font-black text-white">{summary.avg_waiting_time_min} mins</p>
            </div>
          </div>
        </div>

        {/* Analytics Charts split */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Weekly Energy Consumption */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Weekly Grid Load (kWh)</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={weeklyEnergy} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorGrid" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" stroke="#64748b" style={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" style={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <Area type="monotone" dataKey="energy" stroke="#22d3ee" fillOpacity={1} fill="url(#colorGrid)" strokeWidth={2.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Peak Hours distribution */}
          <div className="glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Peak Hour Session Distribution</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={peakHours} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="hour" stroke="#64748b" style={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" style={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                  <Bar dataKey="sessions" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default Analytics;
