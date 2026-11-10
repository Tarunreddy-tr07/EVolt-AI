import React, { useState, useEffect } from 'react';
import { Car, Fuel, Gauge, Thermometer, BatteryLow, Cpu, RefreshCw, CheckCircle2 } from 'lucide-react';
import { vehicleService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const MyEV: React.FC = () => {
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Registration Form
  const [model, setModel] = useState('');
  const [capacity, setCapacity] = useState('75');
  const [chargeType, setChargeType] = useState('DC');
  const [registerSuccess, setRegisterSuccess] = useState(false);

  useEffect(() => {
    fetchVehicles();
  }, []);

  const fetchVehicles = async () => {
    setLoading(true);
    try {
      const list = await vehicleService.getVehicles();
      setVehicles(list);
      if (list.length > 0) {
        setModel(list[0].vehicle_model);
        setCapacity(list[0].battery_capacity.toString());
        setChargeType(list[0].charging_type);
      }
    } catch (err) {
      setError('Failed to fetch registered vehicles.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!model || !capacity) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);
    setRegisterSuccess(false);
    try {
      await vehicleService.addVehicle({
        vehicle_model: model,
        battery_capacity: parseFloat(capacity),
        current_soc: 45.0,
        current_soh: 100.0,
        battery_temperature: 25.0,
        charging_type: chargeType
      });
      setRegisterSuccess(true);
      fetchVehicles();
    } catch (err) {
      setError('Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && vehicles.length === 0) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Electric Vehicle Profiles</h1>
          <p className="text-gray-400 text-sm mt-1">Manage battery sizes, connector types, and telemetry nodes.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Active EV Card */}
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider">Registered Vehicles</h3>

            {vehicles.length > 0 ? (
              vehicles.map((v) => (
                <div key={v.id} className="glass-panel p-6 rounded-2xl relative overflow-hidden group border border-[#334155]/60 hover:border-cyan-500/30 transition">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-400/5 rounded-full blur-2xl pointer-events-none"></div>
                  
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex items-center gap-4">
                      <div className="p-4 bg-cyan-500/10 rounded-2xl text-cyan-400 border border-cyan-500/20">
                        <Car className="w-8 h-8" />
                      </div>
                      <div>
                        <h4 className="text-xl font-bold text-white">{v.vehicle_model}</h4>
                        <p className="text-xs text-gray-500 mt-1">ID Ref: EV-{v.id.toString().padStart(2, '0')} | Connector: {v.charging_type}</p>
                      </div>
                    </div>
                    <span className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider">
                      Active
                    </span>
                  </div>

                  {/* Battery detailed specs grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-8 pt-6 border-t border-[#334155]/60">
                    <div>
                      <p className="text-[10px] text-gray-500 font-semibold uppercase">Capacity</p>
                      <p className="text-base font-bold text-white mt-1">{v.battery_capacity} kWh</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-semibold uppercase">Current SOC</p>
                      <p className="text-base font-bold text-cyan-400 mt-1">{v.current_soc}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-semibold uppercase">Battery SOH</p>
                      <p className="text-base font-bold text-emerald-400 mt-1">{v.current_soh}%</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-semibold uppercase">Thermal State</p>
                      <p className="text-base font-bold text-amber-400 mt-1">{v.battery_temperature}°C</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="glass-panel p-12 rounded-2xl text-center text-gray-500">
                <BatteryLow className="w-12 h-12 text-gray-600 mb-3 mx-auto" />
                <p className="text-sm font-medium">No vehicles registered under this account.</p>
              </div>
            )}
          </div>

          {/* Registration form sidebar */}
          <div className="lg:col-span-1 glass-panel p-6 rounded-2xl h-fit">
            <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Register New EV</h3>

            {error && <p className="text-red-400 text-xs py-2">{error}</p>}
            {registerSuccess && (
              <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>EV Profile Created Successfully!</span>
              </div>
            )}

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-gray-300 text-xs font-medium mb-1.5">Vehicle Model</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <Car className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    placeholder="Tesla Model Y"
                    className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-300 text-xs font-medium mb-1.5">Capacity (kWh)</label>
                  <div className="relative">
                    <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                      <Gauge className="w-4 h-4" />
                    </span>
                    <input
                      type="number"
                      value={capacity}
                      onChange={(e) => setCapacity(e.target.value)}
                      placeholder="82"
                      className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-gray-300 text-xs font-medium mb-1.5">Charging Type</label>
                  <select
                    value={chargeType}
                    onChange={(e) => setChargeType(e.target.value)}
                    className="w-full bg-[#0f172a] border border-[#334155] px-3 py-2.5 rounded-xl text-xs text-white focus:outline-none"
                  >
                    <option value="DC">DC Fast</option>
                    <option value="AC">AC Slow</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:opacity-90 text-black font-extrabold rounded-xl transition text-xs flex items-center justify-center gap-2"
              >
                <Cpu className="w-4 h-4" /> Register Vehicle
              </button>
            </form>
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default MyEV;
