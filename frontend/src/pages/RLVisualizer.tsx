import React, { useState, useEffect } from 'react';
import { ArrowRight, RefreshCw, Layers, ShieldCheck, Sparkles } from 'lucide-react';
import { rlService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const RLVisualizer: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const logs = await rlService.getHistory();
      setHistory(logs);
    } catch (err) {
      console.error('Error fetching decision logs:', err);
    } finally {
      setLoading(false);
    }
  };

  // Mock Q-Table Matrix dataset for the presentation
  const mockQTable = [
    { state: 'SOC: Low, Price: High, Queue: Short', charge_now: 3.42, wait: 6.81, fast_charge: 1.15, slow_charge: 4.88, change_station: 2.19 },
    { state: 'SOC: Low, Price: Low, Queue: Short', charge_now: 8.52, wait: -2.31, fast_charge: 9.78, slow_charge: 5.12, change_station: -0.45 },
    { state: 'SOC: High, Price: High, Queue: Long', charge_now: -4.20, wait: 8.44, fast_charge: -9.50, slow_charge: 1.20, change_station: 6.75 },
    { state: 'SOC: Mid, Price: Normal, Queue: Short', charge_now: 5.22, wait: 3.10, fast_charge: 3.44, slow_charge: 7.95, change_station: 1.05 },
    { state: 'SOC: Low, Temp: Hot, Queue: Long', charge_now: -1.25, wait: 5.42, fast_charge: -8.50, slow_charge: 2.10, change_station: 8.11 }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">RL Environment & Policy Visualizer</h1>
          <p className="text-gray-400 text-sm mt-1">Interactive educational pipeline illustrating states, actions, rewards, and Q-tables.</p>
        </div>

        {/* MDP Interactive Visual Loops */}
        <div className="glass-panel p-8 rounded-2xl relative overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-400/5 rounded-full blur-[100px] pointer-events-none"></div>
          
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider">Markov Decision Process Loop (MDP)</h3>
            <button onClick={fetchHistory} className="text-gray-400 hover:text-white flex items-center gap-1 text-xs">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh Trace
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-5 items-center gap-4 text-center">
            
            <div className="bg-[#0f172a] p-4 rounded-xl border border-cyan-500/20 w-full relative group">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-cyan-500 text-black font-extrabold text-[8px] px-2 py-0.5 rounded-full uppercase tracking-wider">
                State (S)
              </span>
              <div className="space-y-1 text-left text-xs text-gray-400 mt-2">
                <p>SOC: <strong className="text-white">28%</strong></p>
                <p>SOH: <strong className="text-white">94%</strong></p>
                <p>Temp: <strong className="text-white">31°C</strong></p>
                <p>Price: <strong className="text-white">₹8.5/kWh</strong></p>
              </div>
            </div>

            <div className="flex justify-center"><ArrowRight className="w-6 h-6 text-cyan-400" /></div>

            <div className="bg-[#0f172a] p-4 rounded-xl border border-emerald-500/20 w-full relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500 text-black font-extrabold text-[8px] px-2 py-0.5 rounded-full uppercase tracking-wider">
                Action (A)
              </span>
              <p className="text-lg font-black text-white mt-2">SLOW CHARGE</p>
              <p className="text-[10px] text-gray-500 mt-1">Softmax confidence: 82%</p>
            </div>

            <div className="flex justify-center"><ArrowRight className="w-6 h-6 text-emerald-400" /></div>

            <div className="bg-[#0f172a] p-4 rounded-xl border border-purple-500/20 w-full relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500 text-black font-extrabold text-[8px] px-2 py-0.5 rounded-full uppercase tracking-wider">
                Reward (R)
              </span>
              <p className="text-3xl font-black text-purple-400 mt-1">+8.70</p>
              <p className="text-[9px] text-gray-500 mt-1">Cost penalty avoided</p>
            </div>

          </div>
        </div>

        {/* Q-Value Table matrix */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex items-center gap-2 mb-6">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-lg text-white">Q-Value Function Approximation Matrix</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-[#334155]/60 text-gray-400 text-xs">
                  <th className="pb-3 font-semibold">DISCRETIZED STATE SPACE BINS</th>
                  <th className="pb-3 font-semibold text-right">CHARGE NOW</th>
                  <th className="pb-3 font-semibold text-right">WAIT / IDLE</th>
                  <th className="pb-3 font-semibold text-right">FAST CHARGE</th>
                  <th className="pb-3 font-semibold text-right">SLOW CHARGE</th>
                  <th className="pb-3 font-semibold text-right">CHANGE STATION</th>
                </tr>
              </thead>
              <tbody>
                {mockQTable.map((row, idx) => (
                  <tr key={idx} className="border-b border-[#334155]/40 hover:bg-[#1e293b]/20 transition">
                    <td className="py-4 text-xs font-semibold text-gray-300">{row.state}</td>
                    <td className="py-4 text-right font-mono text-xs">{row.charge_now.toFixed(2)}</td>
                    <td className="py-4 text-right font-mono text-xs">{row.wait.toFixed(2)}</td>
                    <td className="py-4 text-right font-mono text-xs">{row.fast_charge.toFixed(2)}</td>
                    <td className="py-4 text-right font-mono text-xs text-cyan-400 font-bold">{row.slow_charge.toFixed(2)}</td>
                    <td className="py-4 text-right font-mono text-xs">{row.change_station.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent RL decisions list */}
        <div className="glass-panel p-6 rounded-2xl">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-lg text-white">Live Decision Audit Logs</h3>
          </div>

          {loading ? (
            <div className="text-center py-6">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-cyan-400 mx-auto"></div>
            </div>
          ) : history.length > 0 ? (
            <div className="space-y-4">
              {history.map((log) => (
                <div key={log.id} className="p-4 bg-[#0f172a]/60 border border-[#334155]/60 rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-xs">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-cyan-400 uppercase">{log.selected_action}</span>
                      <span className="text-gray-500">|</span>
                      <span className="text-gray-400">Reward: {log.reward}</span>
                    </div>
                    <p className="text-gray-500">Logged on {new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                  <div className="text-gray-400 md:max-w-md">
                    {log.explanation.map((e: string, i: number) => (
                      <p key={i}>• {e}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm text-center py-6">No RL decision records logged in SQLite database.</p>
          )}
        </div>

      </div>
    </DashboardLayout>
  );
};

export default RLVisualizer;
