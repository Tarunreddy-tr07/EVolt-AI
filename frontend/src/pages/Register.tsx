import React, { useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, Car, Gauge, BrainCircuit, Loader2, BatteryCharging, Zap } from 'lucide-react';
import { authService, vehicleService } from '../services/api';
import chargingBackground from '../assets/ev-charging-background.png';

const getApiErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error !== 'object' || error === null || !('response' in error)) return fallback;

  const response = (error as { response?: { data?: { detail?: unknown } } }).response;
  const detail = response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .join(', ');
  }
  return fallback;
};

const EV_MODELS = [
  'Tesla Model 3 Long Range',
  'Tesla Model Y',
  'Tesla Model S',
  'Tesla Model X',
  'Tata Nexon EV',
  'Tata Tigor EV',
  'MG ZS EV',
  'Hyundai Ioniq 5',
  'Hyundai Kona Electric',
  'Kia EV6',
  'BYD Atto 3',
  'BYD e6',
  'Mahindra XUV400 EV',
  'BMW i4',
  'Mercedes-Benz EQB',
];

const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [evModel, setEvModel] = useState('Tesla Model 3 Long Range');
  const [batteryCapacity, setBatteryCapacity] = useState('75');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isModelFocused, setIsModelFocused] = useState(false);
  const [highlightedModel, setHighlightedModel] = useState(0);
  const navigate = useNavigate();
  const modelSuggestions = useMemo(() => {
    const query = evModel.trim().toLowerCase();
    return EV_MODELS.filter((model) => model.toLowerCase().includes(query)).slice(0, 6);
  }, [evModel]);

  const selectModel = (model: string) => {
    setEvModel(model);
    setIsModelFocused(false);
  };

  const handleModelKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isModelFocused || modelSuggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedModel((current) => (current + 1) % modelSuggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedModel((current) => (current - 1 + modelSuggestions.length) % modelSuggestions.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      selectModel(modelSuggestions[highlightedModel]);
    } else if (e.key === 'Escape') {
      setIsModelFocused(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password || !evModel || !batteryCapacity) {
      setError('Please fill in all fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // 1. Register the user
      await authService.register({ name, email, password });
      
      // 2. Perform login automatically to retrieve JWT token
      const tokenData = await authService.login({ email, password });
      localStorage.setItem('token', tokenData.access_token);
      
      // 3. Add their primary vehicle
      await vehicleService.addVehicle({
        vehicle_model: evModel,
        battery_capacity: parseFloat(batteryCapacity),
        current_soc: 30.0,
        current_soh: 100.0,
        battery_temperature: 25.0,
        charging_type: 'DC'
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);

    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Registration failed. Please check your parameters.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center px-4 relative overflow-hidden py-12">
      <div
        className="realistic-charging-background"
        style={{ backgroundImage: `url(${chargingBackground})` }}
        aria-hidden="true"
      />
      <div className="charging-backdrop" aria-hidden="true">
        <div className="charging-horizon"></div>
        <div className="charging-road"></div>
        <div className="charging-orb charging-orb-cyan"></div>
        <div className="charging-orb charging-orb-green"></div>
        <div className="charging-station">
          <div className="charging-station-header">
            <BatteryCharging className="h-7 w-7 text-cyan-300" />
            <span>CHARGE</span>
          </div>
          <div className="charging-station-screen">
            <span>84%</span>
            <div className="charging-progress"><span></span></div>
          </div>
          <div className="charging-cable"></div>
        </div>
        <div className="charging-car">
          <div className="charging-car-roof"></div>
          <div className="charging-car-window"></div>
          <div className="charging-car-body"><Zap className="h-5 w-5 text-cyan-300" /></div>
          <span className="charging-wheel charging-wheel-left"></span>
          <span className="charging-wheel charging-wheel-right"></span>
        </div>
        <span className="charging-particle particle-one"></span>
        <span className="charging-particle particle-two"></span>
        <span className="charging-particle particle-three"></span>
      </div>
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="w-full max-w-lg register-card glass-panel p-8 rounded-2xl relative z-10">
        {/* Header/Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-cyan-500/10 rounded-2xl mb-3 border border-cyan-500/20">
            <BrainCircuit className="w-8 h-8 text-cyan-400" />
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            Create Account
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Build your smart microgrid driver profile
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl text-sm text-center">
            Registration successful! Redirecting to dashboard console...
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Full Name</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <User className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Tarun"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Email Address</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tarun@example.com"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition text-sm"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-1">Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">EV Model</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Car className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  value={evModel}
                  onChange={(e) => {
                    setEvModel(e.target.value);
                    setHighlightedModel(0);
                    setIsModelFocused(true);
                  }}
                  onFocus={() => {
                    setHighlightedModel(0);
                    setIsModelFocused(true);
                  }}
                  onKeyDown={handleModelKeyDown}
                  placeholder="Tesla Model 3"
                  role="combobox"
                  aria-expanded={isModelFocused && modelSuggestions.length > 0}
                  aria-controls="ev-model-suggestions"
                  aria-autocomplete="list"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition text-sm"
                />
                {isModelFocused && modelSuggestions.length > 0 && (
                  <div
                    id="ev-model-suggestions"
                    role="listbox"
                    className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-xl border border-[#334155] bg-[#111827] shadow-xl"
                  >
                    {modelSuggestions.map((model, index) => (
                      <button
                        key={model}
                        type="button"
                        role="option"
                        aria-selected={index === highlightedModel}
                        onMouseDown={(e) => e.preventDefault()}
                        onClick={() => selectModel(model)}
                        className={`block w-full px-4 py-2.5 text-left text-sm transition ${
                          index === highlightedModel
                            ? 'bg-cyan-500/15 text-cyan-300'
                            : 'text-gray-300 hover:bg-white/5 hover:text-white'
                        }`}
                      >
                        {model}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-medium mb-1">Battery Capacity (kWh)</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Gauge className="w-4 h-4" />
                </span>
                <input
                  type="number"
                  value={batteryCapacity}
                  onChange={(e) => setBatteryCapacity(e.target.value)}
                  placeholder="75"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0f172a]/80 border border-[#334155] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition text-sm"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="w-full py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-black font-semibold rounded-xl transition flex items-center justify-center gap-2 disabled:opacity-50 mt-6 text-sm"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating Profile...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Footer links */}
        <div className="text-center mt-6">
          <p className="text-gray-400 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-cyan-400 hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
