import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Battery, AlertTriangle, ArrowRight, Timer, Info, HelpCircle,
  HelpCircle as HelpIcon, Sparkles, Navigation, ShieldCheck, Thermometer
} from 'lucide-react';
import { authService, vehicleService, rlService, batteryService, stationService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const Dashboard: React.FC = () => {
  const [vehicle, setVehicle] = useState<any>(null);
  const [userName, setUserName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  // Editable simulation variables for presentation testing
  const [simPrice, setSimPrice] = useState(8.5);
  const [simQueue, setSimQueue] = useState(2);
  const [simAvail, setSimAvail] = useState(4);
  const [simDistance, setSimDistance] = useState(3.2);

  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [user, vehicles] = await Promise.all([
        authService.getMe(),
        vehicleService.getVehicles(),
      ]);
      setUserName(user.name);
      if (vehicles && vehicles.length > 0) {
        const v = vehicles[0];
        setVehicle(v);
        // Load recommendation using the vehicle's parameters and our default simulation states
        triggerRLRecommendation(v, simPrice, simQueue, simAvail, simDistance);
      } else {
        setError('No vehicles found. Please add a vehicle first.');
      }
    } catch (err) {
      setError('Failed to load dashboard parameters.');
    } finally {
      setLoading(false);
    }
  };

  const triggerRLRecommendation = async (
    v: any,
    price: number,
    queue: number,
    avail: number,
    dist: number
  ) => {
    setLoadingRec(true);
    try {
      const rec = await rlService.getRecommendation({
        soc: v.current_soc,
        soh: v.current_soh,
        temperature: v.battery_temperature,
        electricity_price: price,
        queue_length: queue,
        charger_availability: avail,
        distance: dist,
        charging_demand: v.battery_capacity * (1.0 - v.current_soc / 100.0) // energy needed
      });
      setRecommendation(rec);
    } catch (err) {
      console.error('Error fetching RL recommendation:', err);
    } finally {
      setLoadingRec(false);
    }
  };

  const handleSimValueChange = () => {
    if (vehicle) {
      triggerRLRecommendation(vehicle, simPrice, simQueue, simAvail, simDistance);
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

  // Calculate battery gauge percentage layout
  const strokeDashoffset = vehicle ? 440 - (440 * vehicle.current_soc) / 100 : 440;

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Upper greeting & stats header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">
              Good Morning, {userName || 'there'}
            </h1>
            <p className="text-gray-400 text-sm mt-1">Here is your EV battery and microgrid status today.</p>
          </div>
          
          <button
            onClick={() => navigate('/live-charging')}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-emerald-500 text-black font-bold rounded-xl transition hover:opacity-90 shadow-md"
          >
            Start Charging Simulation <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        {/* Core content grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* Battery circular gauge card */}
          <div className="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden group">
            <h3 className="text-gray-400 font-semibold text-sm uppercase self-start mb-6">Battery Telemetry</h3>
            
            <div className="relative w-48 h-48 flex items-center justify-center">
              {/* Circular progress bar SVG */}
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="96" cy="96" r="70" className="stroke-[#1e293b]" strokeWidth="12" fill="transparent" />
                <circle
                  cx="96"
                  cy="96"
                  r="70"
                  className="stroke-cyan-400 transition-all duration-500"
                  strokeWidth="12"
                  fill="transparent"
                  strokeDasharray="440"
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                />
              </svg>
              
              {/* Center text */}
              <div className="absolute text-center">
                <p className="text-5xl font-black">{vehicle?.current_soc}%</p>
                <p className="text-xs text-cyan-400 uppercase tracking-widest font-semibold mt-1">SoC</p>
              </div>
            </div>

            {/* Sub-KPI grids */}
            <div className="grid grid-cols-2 w-full gap-4 mt-8 pt-6 border-t border-[#334155]/60 text-center">
              <div>
                <p className="text-xs text-gray-500 font-semibold uppercase">State of Health</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">{vehicle?.current_soh}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 font-semibold uppercase">Estimated Range</p>
                <p className="text-xl font-bold text-white mt-1">
                  {vehicle ? Math.round(vehicle.battery_capacity * 4.8 * (vehicle.current_soc / 100)) : 0} km
                </p>
              </div>
            </div>

            {/* Battery thermal indicator */}
            <div className="flex items-center gap-2 mt-4 px-3 py-1 bg-amber-500/10 border border-amber-500/25 rounded-full text-xs text-amber-400">
              <Thermometer className="w-3.5 h-3.5" />
              <span>Temp: <strong>{vehicle?.battery_temperature}°C</strong> (Stable)</span>
            </div>
          </div>

          {/* AI Recommendation Card (Centered Highlight) */}
          <div className="xl:col-span-2 bg-gradient-to-br from-[#1e293b] via-[#101b2a] to-[#0f172a] border border-cyan-500/35 p-6 rounded-2xl relative shadow-2xl overflow-hidden group">
            {/* Glossy radial spotlight */}
            <div className="absolute -top-1/4 -right-1/4 w-80 h-80 bg-cyan-400/10 rounded-full blur-[80px]"></div>
            
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
                <h3 className="font-extrabold text-lg text-white">AI Smart Charging Recommendation</h3>
              </div>
              <span className="bg-cyan-500 text-black font-extrabold text-[10px] px-2.5 py-0.5 rounded-full uppercase tracking-wider shadow">
                RL Active
              </span>
            </div>

            {loadingRec ? (
              <div className="flex flex-col items-center justify-center h-48 gap-3">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400"></div>
                <p className="text-sm text-gray-400">RL Agent evaluating state values...</p>
              </div>
            ) : recommendation ? (
              <div className="space-y-6">
                
                {/* Decision metrics row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#0f172a]/60 p-4 rounded-xl border border-[#334155]/60">
                  <div>
                    <p className="text-xs text-gray-500 font-semibold uppercase">Recommended Action</p>
                    <p className="text-lg font-black text-cyan-300 mt-1">{recommendation.action.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-semibold uppercase">Estimated Cost</p>
                    <p className="text-lg font-black text-emerald-400 mt-1">₹{recommendation.estimated_cost}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-semibold uppercase">Estimated Wait</p>
                    <p className="text-lg font-black text-amber-400 mt-1">{recommendation.estimated_wait} mins</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 font-semibold uppercase">Agent Confidence</p>
                    <p className="text-lg font-black text-purple-400 mt-1">{Math.round(recommendation.confidence * 100)}%</p>
                  </div>
                </div>

                {/* Explanation text drop down */}
                <div className="space-y-2">
                  <button
                    onClick={() => setShowExplanation(!showExplanation)}
                    className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-cyan-400 transition"
                  >
                    <Info className="w-4 h-4" />
                    <span>Why did the RL agent select this action? (Expand details)</span>
                  </button>
                  
                  {showExplanation && (
                    <div className="p-4 bg-[#0b0f19] border border-[#334155] rounded-xl text-sm text-gray-300 space-y-2 animate-fadeIn">
                      <p className="font-semibold text-white mb-2 text-xs uppercase tracking-wider text-cyan-400">Agent Reason Logs:</p>
                      {recommendation.reason.map((r: string, idx: number) => (
                        <p key={idx} className="flex items-center gap-2 text-xs">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                          {r}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => navigate('/smart-charging')}
                    className="flex-1 py-3 bg-cyan-500 hover:bg-cyan-600 text-black font-extrabold rounded-xl transition shadow shadow-cyan-500/20 text-sm"
                  >
                    Start Smart Charging Session
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-sm text-center py-12">No recommendation available.</p>
            )}
          </div>
        </div>

        {/* Presentation Simulation controls widget */}
        <div className="glass-panel p-6 rounded-2xl space-y-6">
          <div>
            <h3 className="font-bold text-lg text-white">RL Environment Simulator</h3>
            <p className="text-gray-400 text-xs mt-1">Adjust microgrid state variables to trigger dynamic RL updates.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label className="flex justify-between text-xs text-gray-400 font-semibold mb-2">
                <span>ELECTRICITY PRICE (₹/kWh)</span>
                <span className="text-cyan-400">₹{simPrice.toFixed(1)}</span>
              </label>
              <input
                type="range"
                min="5"
                max="15"
                step="0.5"
                value={simPrice}
                onChange={(e) => { setSimPrice(parseFloat(e.target.value)); handleSimValueChange(); }}
                className="w-full accent-cyan-400"
              />
            </div>

            <div>
              <label className="flex justify-between text-xs text-gray-400 font-semibold mb-2">
                <span>STATION QUEUE</span>
                <span className="text-amber-400">{simQueue} Vehicles</span>
              </label>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={simQueue}
                onChange={(e) => { setSimQueue(parseInt(e.target.value)); handleSimValueChange(); }}
                className="w-full accent-cyan-400"
              />
            </div>

            <div>
              <label className="flex justify-between text-xs text-gray-400 font-semibold mb-2">
                <span>AVAILABLE CHARGERS</span>
                <span className="text-emerald-400">{simAvail} Plugs</span>
              </label>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={simAvail}
                onChange={(e) => { setSimAvail(parseInt(e.target.value)); handleSimValueChange(); }}
                className="w-full accent-cyan-400"
              />
            </div>

            <div>
              <label className="flex justify-between text-xs text-gray-400 font-semibold mb-2">
                <span>DISTANCE TO HUB (KM)</span>
                <span className="text-purple-400">{simDistance.toFixed(1)} km</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="10"
                step="0.5"
                value={simDistance}
                onChange={(e) => { setSimDistance(parseFloat(e.target.value)); handleSimValueChange(); }}
                className="w-full accent-cyan-400"
              />
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
