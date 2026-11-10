import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BrainCircuit, Coins, Clock, HeartPulse, Sparkles, HelpCircle,
  HelpCircle as HelpIcon, ArrowRight, Zap, RefreshCw, Layers
} from 'lucide-react';
import { vehicleService, rlService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const SmartCharging: React.FC = () => {
  const [vehicle, setVehicle] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Custom states for simulation
  const [agentType, setAgentType] = useState<'DQN' | 'Q-LEARNING'>('DQN');
  const [simPrice, setSimPrice] = useState(8.5);
  const [simQueue, setSimQueue] = useState(2);
  const [simAvail, setSimAvail] = useState(4);
  const [simDistance, setSimDistance] = useState(3.2);

  useEffect(() => {
    fetchData();
  }, [agentType]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const vehicles = await vehicleService.getVehicles();
      if (vehicles && vehicles.length > 0) {
        const v = vehicles[0];
        setVehicle(v);
        
        // Fetch RL evaluation
        const rec = await rlService.getRecommendation({
          soc: v.current_soc,
          soh: v.current_soh,
          temperature: v.battery_temperature,
          electricity_price: simPrice,
          queue_length: simQueue,
          charger_availability: simAvail,
          distance: simDistance,
          charging_demand: v.battery_capacity * (1.0 - v.current_soc / 100.0)
        });
        setRecommendation(rec);
      } else {
        setError('No registered vehicle found. Add one in My EV.');
      }
    } catch (err) {
      setError('Failed to query RL decision metrics.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateUpdate = async () => {
    if (!vehicle) return;
    setLoading(true);
    try {
      const rec = await rlService.getRecommendation({
        soc: vehicle.current_soc,
        soh: vehicle.current_soh,
        temperature: vehicle.battery_temperature,
        electricity_price: simPrice,
        queue_length: simQueue,
        charger_availability: simAvail,
        distance: simDistance,
        charging_demand: vehicle.battery_capacity * (1.0 - vehicle.current_soc / 100.0),
        agent_type: agentType
      });
      setRecommendation(rec);
    } catch (err) {
      setError('Failed to update simulation decision.');
    } finally {
      setLoading(false);
    }
  };

  const actionComparison = [
    { id: 'CHARGE_NOW', name: 'Charge Now', rate: 'Standard AC', cost: '₹200 - ₹350', wait: 'Queue-based', impact: 'Moderate', color: 'text-blue-400' },
    { id: 'WAIT', name: 'Wait / Idle', rate: 'Decline', cost: '₹0.0', wait: '15 mins', impact: 'Safe / None', color: 'text-amber-400' },
    { id: 'FAST_CHARGE', name: 'Fast Charge', rate: 'DC 50 kW', cost: '₹400 - ₹600', wait: 'Priority', impact: 'Thermal wear', color: 'text-red-400' },
    { id: 'SLOW_CHARGE', name: 'Slow Charge', rate: 'AC 7.4 kW', cost: '₹120 - ₹200', wait: 'Dwell-based', impact: 'Battery friendly', color: 'text-emerald-400' },
    { id: 'CHANGE_STATION', name: 'Change Station', rate: 'Seek Alternative', cost: 'Travel cost', wait: 'Distance-based', impact: 'Safe / None', color: 'text-purple-400' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        
        {/* Header section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Smart Charging Control Center</h1>
            <p className="text-gray-400 text-sm mt-1">Audit the neural network policy parameters and microgrid environmental inputs.</p>
          </div>

          {/* Model selector toggles */}
          <div className="flex bg-[#0f172a] border border-[#334155] rounded-xl p-1">
            <button
              onClick={() => setAgentType('DQN')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                agentType === 'DQN'
                  ? 'bg-cyan-500 text-black shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Deep Q-Network (DQN)
            </button>
            <button
              onClick={() => setAgentType('Q-LEARNING')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                agentType === 'Q-LEARNING'
                  ? 'bg-cyan-500 text-black shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Q-Learning Baseline
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        {/* State vectors display panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <div className="lg:col-span-1 glass-panel p-6 rounded-2xl space-y-6">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider">Current State Vector (S)</h3>
            
            {vehicle && (
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b border-[#334155]/40 text-sm">
                  <span className="text-gray-400">State of Charge (SOC)</span>
                  <span className="font-bold text-white">{vehicle.current_soc}%</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-[#334155]/40 text-sm">
                  <span className="text-gray-400">State of Health (SOH)</span>
                  <span className="font-bold text-emerald-400">{vehicle.current_soh}%</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-[#334155]/40 text-sm">
                  <span className="text-gray-400">Battery Temp</span>
                  <span className="font-bold text-amber-400">{vehicle.battery_temperature}°C</span>
                </div>
                
                {/* Simulated variables controls */}
                <div className="pt-4 space-y-4">
                  <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-widest">Environment Controls</h4>
                  <div>
                    <label className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>Tariff Price</span>
                      <span>₹{simPrice.toFixed(1)}</span>
                    </label>
                    <input type="range" min="5" max="15" step="0.5" value={simPrice} onChange={(e) => setSimPrice(parseFloat(e.target.value))} className="w-full accent-cyan-400" />
                  </div>
                  <div>
                    <label className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>Station Queue</span>
                      <span>{simQueue} vehicles</span>
                    </label>
                    <input type="range" min="0" max="10" step="1" value={simQueue} onChange={(e) => setSimQueue(parseInt(e.target.value))} className="w-full accent-cyan-400" />
                  </div>
                  <div>
                    <label className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>Charger Availability</span>
                      <span>{simAvail} plugs</span>
                    </label>
                    <input type="range" min="0" max="10" step="1" value={simAvail} onChange={(e) => setSimAvail(parseInt(e.target.value))} className="w-full accent-cyan-400" />
                  </div>
                  <div>
                    <label className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>Distance to Station</span>
                      <span>{simDistance.toFixed(1)} km</span>
                    </label>
                    <input type="range" min="0.5" max="10" step="0.5" value={simDistance} onChange={(e) => setSimDistance(parseFloat(e.target.value))} className="w-full accent-cyan-400" />
                  </div>
                </div>

                <button
                  onClick={handleSimulateUpdate}
                  className="w-full py-3 bg-[#1e293b] border border-cyan-500/30 hover:border-cyan-400 text-cyan-400 font-bold rounded-xl transition flex items-center justify-center gap-2 text-sm"
                >
                  <RefreshCw className="w-4 h-4" /> Evaluate State Changes
                </button>
              </div>
            )}
          </div>

          {/* Action spaces and Q-value calculations */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Explaining MDP step */}
            <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
              <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Markov Decision Process Flow (MDP)</h3>
              
              <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-center">
                <div className="bg-[#0f172a] p-4 rounded-xl border border-[#334155] w-full md:w-32">
                  <p className="text-xs text-gray-500 font-bold">STATE (S)</p>
                  <p className="text-sm font-black mt-1 text-white">8 parameters</p>
                </div>
                
                <ArrowRight className="w-5 h-5 text-gray-500 hidden md:block" />
                
                <div className="bg-cyan-500/10 p-4 rounded-xl border border-cyan-400/40 w-full md:w-40">
                  <p className="text-xs text-cyan-400 font-bold">RL POLICY (π)</p>
                  <p className="text-sm font-black mt-1 text-white">{agentType} Model</p>
                </div>

                <ArrowRight className="w-5 h-5 text-gray-500 hidden md:block" />

                <div className="bg-[#0f172a] p-4 rounded-xl border border-cyan-500/30 shadow-[0_0_15px_rgba(34,211,238,0.15)] w-full md:w-44">
                  <p className="text-xs text-emerald-400 font-bold">ACTION (A)</p>
                  <p className="text-sm font-black mt-1 text-white">{recommendation?.action || 'WAIT'}</p>
                </div>

                <ArrowRight className="w-5 h-5 text-gray-500 hidden md:block" />

                <div className="bg-[#0f172a] p-4 rounded-xl border border-[#334155] w-full md:w-32">
                  <p className="text-xs text-gray-500 font-bold">REWARD (R)</p>
                  <p className="text-sm font-black mt-1 text-white">+{recommendation?.reward || 0.0}</p>
                </div>
              </div>
            </div>

            {/* Action Space Table comparisons */}
            <div className="glass-panel p-6 rounded-2xl">
              <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Action Utilities Comparison</h3>
              
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-[#334155]/60 text-gray-400 text-xs">
                      <th className="pb-3 font-semibold">ACTION</th>
                      <th className="pb-3 font-semibold">CHARGE RATE</th>
                      <th className="pb-3 font-semibold">EST. COST</th>
                      <th className="pb-3 font-semibold">EST. WAIT</th>
                      <th className="pb-3 font-semibold">BATTERY IMPACT</th>
                      <th className="pb-3 font-semibold text-right">Q-VALUE SCORE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {actionComparison.map((act, index) => {
                      const isSelected = recommendation?.action === act.id;
                      const q_val = recommendation?.q_values ? recommendation.q_values[index] : 0.0;
                      return (
                        <tr
                          key={act.id}
                          className={`border-b border-[#334155]/40 transition ${
                            isSelected 
                              ? 'bg-cyan-500/5 border border-cyan-400/40 font-bold text-white shadow-inner'
                              : 'text-gray-300 hover:bg-[#1e293b]/20'
                          }`}
                        >
                          <td className="py-4 pl-2 flex items-center gap-2">
                            {isSelected && <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />}
                            <span className={act.color}>{act.name}</span>
                          </td>
                          <td className="py-4">{act.rate}</td>
                          <td className="py-4">{act.cost}</td>
                          <td className="py-4">{act.wait}</td>
                          <td className="py-4">{act.impact}</td>
                          <td className="py-4 text-right font-mono font-bold text-cyan-400">
                            {q_val.toFixed(3)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default SmartCharging;
