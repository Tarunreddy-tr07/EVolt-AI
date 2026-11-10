import React, { useState, useEffect } from 'react';
import { CalendarRange, Info, Clock, AlertCircle, XCircle } from 'lucide-react';
import { bookingService, stationService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const Bookings: React.FC = () => {
  const [bookings, setBookings] = useState<any[]>([]);
  const [stationsMap, setStationsMap] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const list = await bookingService.getBookings();
      setBookings(list);
      
      const stations = await stationService.getStations();
      const mapping: Record<number, string> = {};
      stations.forEach((st: any) => {
        mapping[st.id] = st.name;
      });
      setStationsMap(mapping);
    } catch (err) {
      setError('Failed to load reservation listings.');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id: number) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;
    try {
      await bookingService.cancelBooking(id);
      fetchBookings();
    } catch (err) {
      setError('Failed to cancel the booking.');
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
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Charging Reservations</h1>
          <p className="text-gray-400 text-sm mt-1">Monitor, modify, or verify slot bookings scheduled at various charging hubs.</p>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl">
            {error}
          </div>
        )}

        <div className="glass-panel p-6 rounded-2xl">
          <h3 className="text-gray-400 font-semibold text-xs uppercase tracking-wider mb-6">Active Reservations</h3>

          {bookings.length > 0 ? (
            <div className="space-y-4">
              {bookings.map((b) => (
                <div
                  key={b.id}
                  className={`p-5 bg-[#0f172a]/60 border rounded-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition ${
                    b.status === 'Cancelled' ? 'opacity-50 border-[#334155]/40' : 'border-[#334155]/60 hover:border-cyan-500/30'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl border ${
                      b.status === 'Cancelled' 
                        ? 'bg-gray-500/10 border-gray-500/25 text-gray-500' 
                        : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                    }`}>
                      <CalendarRange className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-white">{stationsMap[b.station_id] || 'Loading Station...'}</h4>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> {new Date(b.booking_time).toLocaleString()}</span>
                        <span>•</span>
                        <span>Charger #{b.charger_id}</span>
                        <span>•</span>
                        <span>Reference Booking #{b.id.toString().padStart(3, '0')}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-stretch md:self-auto justify-between">
                    <span className={`text-[10px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider border ${
                      b.status === 'Cancelled'
                        ? 'bg-red-500/10 border-red-500/20 text-red-400'
                        : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                    }`}>
                      {b.status}
                    </span>

                    {b.status === 'Confirmed' && (
                      <button
                        onClick={() => handleCancel(b.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10 p-2 rounded-xl transition"
                        title="Cancel Slot"
                      >
                        <XCircle className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle className="w-12 h-12 text-gray-600 mb-3 mx-auto" />
              <p className="text-sm font-medium">No reservation slots booked. Use the Find Stations tab to reserve a charger.</p>
            </div>
          )}
        </div>

      </div>
    </DashboardLayout>
  );
};

export default Bookings;
