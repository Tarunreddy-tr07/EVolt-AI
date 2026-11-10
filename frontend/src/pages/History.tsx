import React, { useState, useEffect } from 'react';
import { History, Coins, Zap, CalendarDays } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { analyticsService, vehicleService, stationService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const HistoryPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [stationsMap, setStationsMap] = useState<Record<number, string>>({});
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
      
      const stations = await stationService.getStations();
      const mapping: Record<number, string> = {};
      stations.forEach((st: any) => {
        mapping[st.id] = st.name;
      });
      setStationsMap(mapping);

      // Fetch a mock list of history rows for display
      const list = [
        { id: 1, station_id: 1, start_time: '2026-08-25T14:30:00Z', duration_min: 45, energy_used: 35.2, cost: 299.2, start_soc: 15, end_soc: 80, status: 'Success' },
        { id: 2, station_id: 2, start_time: '2026-08-22T09:15:00Z', duration_min: 60, energy_used: 48.0, cost: 456.0, start_soc: 10, end_soc: 90, status: 'Success' },
        { id: 3, station_id: 3, start_time: '2026-08-18T18:00:00Z', duration_min: 30, energy_used: 22.4, cost: 224.0, start_soc: 40, end_soc: 75, status: 'Success' },
        { id: 4, station_id: 4, start_time: '2026-08-14T11:45:00Z', duration_min: 45, energy_used: 28.6, cost: 214.5, start_soc: 30, end_soc: 85, status: 'Success' }
      ];
      setSessions(list);
    } catch (err) {
      setError('Failed to fetch historical charging logs.');
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

  // Monthly cost data for bar charts
  const costData = analytics?.charts?.monthly_costs || [];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Charging Logs & Logs</h1>
          <p className="text-gray-400 text-sm mt-1">Audit log of your historical charging sessions, duration logs, and costs.</p>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        {/* Dynamic graphics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Table history list */}
          <div className="lg:col-span-2 glass-panel p-6 rounded-2xl overflow-x-auto">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Historical Sessions</h3>

            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#334155]/60 text-gray-400 font-semibold">
                  <th className="pb-3 pl-2">DATE</th>
                  <th className="pb-3">STATION</th>
                  <th className="pb-3 text-right">ENERGY</th>
                  <th className="pb-3 text-right">COST</th>
                  <th className="pb-3 text-center">SOC SHIFT</th>
                  <th className="pb-3 text-right">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.id} className="border-b border-[#334155]/40 hover:bg-[#1e293b]/20 transition text-gray-300">
                    <td className="py-4 pl-2 font-medium">{new Date(s.start_time).toLocaleDateString()}</td>
                    <td className="py-4 font-bold text-white">{stationsMap[s.station_id] || 'Chennai Central Hub'}</td>
                    <td className="py-4 text-right font-mono">{s.energy_used} kWh</td>
                    <td className="py-4 text-right font-mono text-cyan-400 font-bold">₹{s.cost}</td>
                    <td className="py-4 text-center font-mono">{s.start_soc}% → {s.end_soc}%</td>
                    <td className="py-4 text-right">
                      <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Cost chart column */}
          <div className="lg:col-span-1 glass-panel p-6 rounded-2xl">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Monthly Cost Analytics</h3>

            <div className="h-64 w-full">
              {costData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={costData} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="month" stroke="#64748b" style={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" style={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                    <Bar dataKey="cost" fill="#22d3ee" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                  No cost records found.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default HistoryPage;
