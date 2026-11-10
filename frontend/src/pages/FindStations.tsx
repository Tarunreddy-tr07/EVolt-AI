import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin, Sparkles, SlidersHorizontal, ArrowRight,
  Info, Compass, Coins, Timer, BatteryCharging
} from 'lucide-react';
import { stationService, rlService, vehicleService, bookingService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

// Custom SVG marker icon to prevent Vite relative assets bugs
const cyanMarkerIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2322d3ee" width="32" height="32"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

const FindStations: React.FC = () => {
  const [stations, setStations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [vehicle, setVehicle] = useState<any>(null);
  const [rlRecommendation, setRlRecommendation] = useState<any>(null);
  
  // Selected station drawer
  const [selectedStation, setSelectedStation] = useState<any>(null);
  const [bookingTime, setBookingTime] = useState('10:30');
  const [chargerId, setChargerId] = useState<number | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [bookingError, setBookingError] = useState('');

  // Map settings
  const chennaiCenter: [number, number] = [13.0827, 80.2707];
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const list = await stationService.getStations();
      setStations(list);

      const vehicles = await vehicleService.getVehicles();
      if (vehicles && vehicles.length > 0) {
        const v = vehicles[0];
        setVehicle(v);
        
        // Fetch optimal station recommendations from RL agent
        const rec = await rlService.getRecommendation({
          soc: v.current_soc,
          soh: v.current_soh,
          temperature: v.battery_temperature,
          electricity_price: 8.5,
          queue_length: 2,
          charger_availability: 4,
          distance: 1.5,
          charging_demand: v.battery_capacity * (1.0 - v.current_soc / 100.0)
        });
        setRlRecommendation(rec);
      }
    } catch (err) {
      console.error('Failed to load stations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStationClick = async (station: any) => {
    try {
      const details = await stationService.getStationDetails(station.id);
      setSelectedStation(details);
      setBookingSuccess(false);
      setBookingError('');
      if (details.chargers && details.chargers.length > 0) {
        setChargerId(details.chargers[0].id);
      }
    } catch (err) {
      console.error('Failed to load station chargers:', err);
    }
  };

  const handleBookSlot = async () => {
    if (!chargerId || !selectedStation) return;
    
    // Set booking date/time object
    const bookingDate = new Date();
    const [h, m] = bookingTime.split(':');
    bookingDate.setHours(parseInt(h));
    bookingDate.setMinutes(parseInt(m));
    bookingDate.setSeconds(0);

    try {
      await bookingService.createBooking({
        station_id: selectedStation.id,
        charger_id: chargerId,
        booking_time: bookingDate.toISOString()
      });
      setBookingSuccess(true);
      // Reload stats
      const updatedList = await stationService.getStations();
      setStations(updatedList);
    } catch (err: any) {
      setBookingError(err.response?.data?.detail || 'Booking failed.');
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

  return (
    <DashboardLayout>
      <div className="space-y-6 h-full flex flex-col min-h-[80vh]">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Charging Station Navigator</h1>
          <p className="text-gray-400 text-sm mt-1">Discover, book slots, and navigate to charging hubs using browser GPS markers.</p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 flex-1 items-stretch">
          {/* Map area */}
          <div className="xl:col-span-3 h-[450px] xl:h-auto min-h-[400px] bg-[#0f172a] rounded-2xl border border-[#334155] overflow-hidden relative z-10">
            <MapContainer center={chennaiCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {stations.map((st) => (
                <Marker
                  key={st.id}
                  position={[st.latitude, st.longitude]}
                  icon={cyanMarkerIcon}
                  eventHandlers={{
                    click: () => handleStationClick(st),
                  }}
                >
                  <Popup>
                    <div className="text-white font-sans p-1">
                      <strong className="text-sm block">{st.name}</strong>
                      <span className="text-[10px] text-gray-400 block mt-1">{st.address}</span>
                      <span className="text-xs font-bold text-cyan-400 block mt-2">₹{st.electricity_price}/kWh</span>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>

          {/* Sidebar drawer details */}
          <div className="xl:col-span-1 flex flex-col gap-6 h-full">
            
            {/* AI Recommendation card inside map search */}
            {rlRecommendation && (
              <div className="bg-gradient-to-br from-[#1e293b] to-[#0f172a] border border-cyan-500/25 p-5 rounded-2xl relative shadow overflow-hidden">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <h4 className="font-extrabold text-sm text-white">Recommended Destination</h4>
                </div>
                <p className="text-sm font-bold text-white mb-2">GreenCharge Central Hub</p>
                <div className="flex gap-4 text-xs text-gray-400">
                  <span className="flex items-center gap-1"><Coins className="w-3.5 h-3.5 text-cyan-400" /> ₹8.5/kWh</span>
                  <span className="flex items-center gap-1"><Timer className="w-3.5 h-3.5 text-amber-400" /> Queue: 2</span>
                </div>
              </div>
            )}

            {/* Selected Station detail booking card */}
            {selectedStation ? (
              <div className="glass-panel p-6 rounded-2xl space-y-5 flex-1 select-none flex flex-col justify-between">
                <div>
                  <h3 className="font-black text-lg text-white mb-1">{selectedStation.name}</h3>
                  <p className="text-xs text-gray-400 leading-relaxed mb-4">{selectedStation.address}</p>

                  <div className="grid grid-cols-2 gap-4 py-3 border-y border-[#334155]/60 text-xs mb-4">
                    <div>
                      <p className="text-gray-500 font-semibold uppercase">Electricity tariff</p>
                      <p className="font-black text-sm text-cyan-400 mt-0.5">₹{selectedStation.electricity_price}/kWh</p>
                    </div>
                    <div>
                      <p className="text-gray-500 font-semibold uppercase">Wait time estimate</p>
                      <p className="font-black text-sm text-amber-400 mt-0.5">8 minutes</p>
                    </div>
                  </div>

                  {/* Charger slots selections */}
                  <div className="space-y-3">
                    <label className="block text-xs text-gray-400 font-semibold uppercase">Select Charging Slot</label>
                    <select
                      value={chargerId || ''}
                      onChange={(e) => setChargerId(parseInt(e.target.value))}
                      className="w-full bg-[#0f172a] border border-[#334155] px-3 py-2 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-400"
                    >
                      {selectedStation.chargers.map((c: any) => (
                        <option key={c.id} value={c.id}>
                          Charger #{c.id} ({c.charger_type} DC - {c.power_kw}kW) - {c.status}
                        </option>
                      ))}
                    </select>

                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div>
                        <label className="block text-[10px] text-gray-500 font-bold uppercase mb-1">Time</label>
                        <input
                          type="time"
                          value={bookingTime}
                          onChange={(e) => setBookingTime(e.target.value)}
                          className="w-full bg-[#0f172a] border border-[#334155] px-3 py-2 rounded-xl text-xs text-white"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  {bookingError && <p className="text-red-400 text-xs text-center py-2">{bookingError}</p>}
                  {bookingSuccess ? (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold rounded-xl text-center">
                      Charging Slot Reserved Successfully!
                    </div>
                  ) : (
                    <button
                      onClick={handleBookSlot}
                      className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:opacity-90 text-black font-extrabold rounded-xl transition text-sm flex items-center justify-center gap-2"
                    >
                      <BatteryCharging className="w-4 h-4" /> Reserve Slot Now
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="glass-panel p-8 rounded-2xl flex-1 flex flex-col items-center justify-center text-center text-gray-500 select-none">
                <Compass className="w-12 h-12 text-gray-600 mb-3 animate-spin" style={{ animationDuration: '20s' }} />
                <p className="text-sm font-medium">Select a marker on the map to inspect charging stations and book slots.</p>
              </div>
            )}

          </div>
        </div>

      </div>
    </DashboardLayout>
  );
};

export default FindStations;
