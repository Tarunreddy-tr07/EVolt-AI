import React, { useState, useEffect } from 'react';
import {
  Zap, Clock, ShieldCheck, Flame, Cpu, Gauge, Coins,
  Play, Pause, RotateCcw, AlertTriangle, BatteryCharging,
  ArrowUpRight, Sparkles, Activity, Leaf, TimerReset
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { vehicleService, batteryService } from '../services/api';
import DashboardLayout from '../layouts/DashboardLayout';

const LiveCharging: React.FC = () => {
  const [vehicle, setVehicle] = useState<any>(null);
  const [charging, setCharging] = useState(false);
  const [soc, setSoc] = useState(28.0);
  const [power, setPower] = useState(42.0);
  const [temp, setTemp] = useState(31.0);
  const [energyDelivered, setEnergyDelivered] = useState(0.0);
  const [cost, setCost] = useState(0.0);
  const [timeRemaining, setTimeRemaining] = useState(45);
  const [history, setHistory] = useState<any[]>([]);
  const [step, setStep] = useState(0);

  useEffect(() => {
    vehicleService.getVehicles().then((vehicles) => {
      if (vehicles && vehicles.length > 0) {
        setVehicle(vehicles[0]);
        setSoc(vehicles[0].current_soc);
        setTemp(vehicles[0].battery_temperature);
      }
    });
  }, []);

  useEffect(() => {
    let interval: any = null;
    if (charging) {
      interval = setInterval(() => {
        simulateStep();
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [charging, soc, temp, energyDelivered, cost, step]);

  const simulateStep = () => {
    if (soc >= 98.0) {
      setCharging(false);
      return;
    }

    const nextStep = step + 1;
    const socDelta = power > 15 ? 1.2 : 0.4;
    const newSoc = Math.min(100.0, soc + socDelta);
    const newPower = newSoc > 80.0 ? Math.max(7.4, power - 4.0) : power;
    const newTemp = newSoc > 80.0 ? Math.max(30.0, temp - 0.2) : Math.min(45.0, temp + 0.3);
    const energyDelta = (newPower * 2.0) / 60.0;
    const newEnergy = energyDelivered + energyDelta;
    const newCost = cost + energyDelta * 8.5;
    const minutesLeft = Math.max(0, Math.round(((100.0 - newSoc) * 0.8) / (newPower / 50.0)));

    setSoc(newSoc);
    setPower(newPower);
    setTemp(newTemp);
    setEnergyDelivered(newEnergy);
    setCost(newCost);
    setTimeRemaining(minutesLeft);
    setStep(nextStep);

    const newPoint = {
      time: `${nextStep * 2}s`,
      soc: Math.round(newSoc),
      power: Math.round(newPower),
      temp: Math.round(newTemp),
      energy: parseFloat(newEnergy.toFixed(2)),
    };
    setHistory((previous) => [...previous, newPoint]);

    if (nextStep % 5 === 0 && vehicle) {
      batteryService.recordTelemetry({
        voltage: 380.0 + newSoc * 0.4,
        current: (newPower * 1000) / 380,
        temperature: newTemp,
        soc: Math.round(newSoc),
        soh: vehicle.current_soh,
      });
    }
  };

  const handleReset = () => {
    setCharging(false);
    setSoc(28.0);
    setPower(42.0);
    setTemp(31.0);
    setEnergyDelivered(0.0);
    setCost(0.0);
    setTimeRemaining(45);
    setHistory([]);
    setStep(0);
  };

  const batteryProgress = Math.min(Math.max(soc / 100, 0), 1);
  const ringRadius = 62;
  const ringCircumference = 2 * Math.PI * ringRadius;
  const ringOffset = ringCircumference - batteryProgress * ringCircumference;
  const systemStatus = charging ? (temp > 42 ? 'Thermal protection active' : 'Charging optimally') : (soc >= 98 ? 'Charge complete' : 'Ready to charge');

  const statCards = [
    { label: 'Charge power', value: `${power.toFixed(1)} kW`, detail: '72% of max output', icon: Zap, accent: 'text-cyan-400 bg-cyan-500/10' },
    { label: 'Energy added', value: `${energyDelivered.toFixed(2)} kWh`, detail: 'Grid efficient cycle', icon: BatteryCharging, accent: 'text-emerald-400 bg-emerald-500/10' },
    { label: 'Session cost', value: `₹${cost.toFixed(2)}`, detail: 'Dynamic tariff aware', icon: Coins, accent: 'text-violet-400 bg-violet-500/10' },
    { label: 'Time left', value: `${timeRemaining} min`, detail: `${Math.max(0, 100 - soc).toFixed(0)}% until full`, icon: Clock, accent: 'text-amber-400 bg-amber-500/10' },
  ];

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),transparent_20%),radial-gradient(circle_at_bottom_right,_rgba(52,211,153,0.12),transparent_18%),linear-gradient(135deg,#020817_0%,#0b1220_30%,#111827_100%)]">
        <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
          <div className="rounded-[28px] border border-white/10 bg-slate-950/70 p-5 shadow-[0_30px_80px_rgba(15,23,42,0.8)] backdrop-blur-xl sm:p-6">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.22em] text-cyan-300">
                  <Sparkles className="h-3.5 w-3.5" />
                  Live EV intelligence
                </div>
                <h1 className="text-3xl font-black tracking-tight text-white sm:text-4xl">Charging Session Simulator</h1>
                <p className="mt-2 max-w-2xl text-sm text-slate-300 sm:text-base">
                  Real-time condition monitoring, battery health telemetry, and adaptive charging protection in one premium control panel.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => setCharging(!charging)}
                  className={`inline-flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-bold transition-all duration-200 ${
                    charging
                      ? 'bg-amber-400 text-slate-950 shadow-[0_12px_24px_rgba(251,191,36,0.32)] hover:bg-amber-300'
                      : 'bg-cyan-400 text-slate-950 shadow-[0_12px_24px_rgba(34,211,238,0.3)] hover:bg-cyan-300'
                  }`}
                >
                  {charging ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  {charging ? 'Pause Simulation' : 'Run Simulation'}
                </button>

                <button
                  onClick={handleReset}
                  className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-bold text-slate-100 transition hover:border-white/20 hover:bg-white/10"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </button>
              </div>
            </div>
          </div>

          {temp > 42.0 && (
            <div className="flex items-center gap-3 rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-200 shadow-[0_0_30px_rgba(251,191,36,0.1)]">
              <AlertTriangle className="h-5 w-5 text-amber-300" />
              <span>
                Warning: battery temperature is elevated at <strong>{temp.toFixed(1)}°C</strong>. Smart protection is throttling the charging current.
              </span>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {statCards.map(({ label, value, detail, icon: Icon, accent }) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-[0_16px_30px_rgba(15,23,42,0.25)] backdrop-blur-sm">
                <div className="flex items-center justify-between">
                  <div className={`rounded-xl p-2.5 ${accent}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-slate-500" />
                </div>
                <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">{label}</p>
                <p className="mt-2 text-2xl font-black text-white">{value}</p>
                <p className="mt-1 text-xs text-slate-400">{detail}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.5fr]">
            <div className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.55)]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Vehicle status</p>
                  <h2 className="mt-2 text-2xl font-bold text-white">{systemStatus}</h2>
                </div>
                <div className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-300">
                  {charging ? 'Live' : 'Standby'}
                </div>
              </div>

              <div className="mt-6 flex items-center justify-center">
                <div className="relative flex h-64 w-64 items-center justify-center">
                  <svg className="h-full w-full -rotate-90" viewBox="0 0 160 160" aria-label="Battery charge progress">
                    <circle cx="80" cy="80" r={ringRadius} stroke="rgba(148,163,184,0.22)" strokeWidth="12" fill="none" />
                    <circle
                      cx="80"
                      cy="80"
                      r={ringRadius}
                      stroke={soc >= 80 ? '#34d399' : '#22d3ee'}
                      strokeWidth="12"
                      fill="none"
                      strokeLinecap="round"
                      strokeDasharray={ringCircumference}
                      strokeDashoffset={ringOffset}
                      style={{ transition: 'stroke-dashoffset 0.7s ease' }}
                    />
                  </svg>

                  <div className="absolute inset-8 rounded-full border border-white/10 bg-slate-900/80 shadow-[inset_0_0_40px_rgba(14,116,144,0.18)]">
                    <div className="flex h-full flex-col items-center justify-center">
                      <BatteryCharging className="mb-3 h-7 w-7 text-cyan-300" />
                      <p className="text-4xl font-black text-white">{soc.toFixed(0)}%</p>
                      <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">Battery SoC</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-3 gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <div className="flex items-center gap-2 text-cyan-300">
                    <Gauge className="h-4 w-4" />
                    <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">Voltage</span>
                  </div>
                  <p className="mt-2 text-xl font-black text-white">{(380 + soc * 0.4).toFixed(0)}V</p>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <div className="flex items-center gap-2 text-emerald-300">
                    <Flame className="h-4 w-4" />
                    <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">Current</span>
                  </div>
                  <p className="mt-2 text-xl font-black text-white">{((power * 1000) / 380).toFixed(0)}A</p>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <div className="flex items-center gap-2 text-amber-300">
                    <Cpu className="h-4 w-4" />
                    <span className="text-[10px] font-semibold uppercase tracking-[0.18em]">Temp</span>
                  </div>
                  <p className="mt-2 text-xl font-black text-white">{temp.toFixed(1)}°C</p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.55)]">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Performance</p>
                    <h3 className="mt-2 text-xl font-bold text-white">Charge profile</h3>
                  </div>
                  <div className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-xs font-semibold text-cyan-300">Adaptive</div>
                </div>

                <div className="space-y-4">
                  {[
                    { label: 'Power delivery', value: power, max: 60, color: 'bg-cyan-400', text: 'text-cyan-300' },
                    { label: 'Thermal load', value: temp, max: 45, color: 'bg-amber-400', text: 'text-amber-300' },
                    { label: 'Battery health', value: vehicle?.current_soh ?? 94, max: 100, color: 'bg-emerald-400', text: 'text-emerald-300' },
                  ].map((item) => (
                    <div key={item.label}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="text-slate-300">{item.label}</span>
                        <span className={`font-semibold ${item.text}`}>{item.value.toFixed(0)}{item.label === 'Power delivery' ? ' kW' : item.label === 'Thermal load' ? '°C' : '%'}</span>
                      </div>
                      <div className="h-2.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full ${item.color}`}
                          style={{ width: `${Math.min((item.value / item.max) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.55)]">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Protection stack</p>
                    <h3 className="mt-2 text-xl font-bold text-white">Safety systems</h3>
                  </div>
                  <ShieldCheck className="h-5 w-5 text-emerald-300" />
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    { label: 'Relay', state: 'Active', tone: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20', icon: ShieldCheck },
                    { label: 'Cooling', state: temp > 40 ? 'Boosted' : 'Stable', tone: 'text-cyan-300 bg-cyan-500/10 border-cyan-500/20', icon: Activity },
                    { label: 'Efficiency', state: '92%', tone: 'text-violet-300 bg-violet-500/10 border-violet-500/20', icon: Leaf },
                  ].map(({ label, state, tone, icon: Icon }) => (
                    <div key={label} className={`rounded-2xl border p-3 ${tone}`}>
                      <Icon className="h-4 w-4" />
                      <p className="mt-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-200">{label}</p>
                      <p className="mt-1 text-lg font-black text-white">{state}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-slate-950/60 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.55)]">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Telemetry</p>
                <h3 className="mt-2 text-xl font-bold text-white">Real-time battery curve</h3>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-200">
                <TimerReset className="h-3.5 w-3.5 text-cyan-300" />
                2s sample
              </div>
            </div>

            <div className="h-72 w-full">
              {history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="4 4" />
                    <XAxis dataKey="time" stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: '#020817',
                        border: '1px solid rgba(148,163,184,0.2)',
                        borderRadius: '14px',
                        color: '#e2e8f0',
                      }}
                    />
                    <Line type="monotone" dataKey="soc" name="SoC (%)" stroke="#22d3ee" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="power" name="Power (kW)" stroke="#a78bfa" strokeWidth={2.5} dot={false} />
                    <Line type="monotone" dataKey="temp" name="Temp (°C)" stroke="#fbbf24" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-slate-700 text-sm text-slate-400">
                  Start the charging simulation to view live telemetry.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default LiveCharging;
