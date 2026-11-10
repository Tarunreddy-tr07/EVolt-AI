import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Float } from '@react-three/drei';
import * as THREE from 'three';
import { BrainCircuit, BatteryCharging, ShieldAlert, Cpu } from 'lucide-react';

// Custom 3D Car Chassis using primitives
const FuturisticCar: React.FC = () => {
  const carRef = useRef<THREE.Group>(null);
  const wheelsRef = useRef<THREE.Group>(null);

  // Rotation and floating animations
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (carRef.current) {
      carRef.current.position.y = Math.sin(t * 1.5) * 0.1;
    }
  });

  return (
    <group ref={carRef}>
      {/* Car Base Body */}
      <mesh position={[0, 0.3, 0]} castShadow receiveShadow>
        <boxGeometry args={[3, 0.4, 1.4]} />
        <meshStandardMaterial color="#1e293b" roughness={0.1} metalness={0.9} />
      </mesh>

      {/* Car Cabin Roof (Glassmorphic look) */}
      <mesh position={[-0.2, 0.65, 0]} castShadow>
        <boxGeometry args={[1.5, 0.4, 1.1]} />
        <meshStandardMaterial color="#22d3ee" transparent opacity={0.6} roughness={0.0} metalness={1.0} />
      </mesh>

      {/* Futuristic Neo LED Front Headlights */}
      <mesh position={[1.51, 0.3, 0.4]}>
        <boxGeometry args={[0.02, 0.1, 0.3]} />
        <meshStandardMaterial color="#34d399" emissive="#34d399" emissiveIntensity={5} />
      </mesh>
      <mesh position={[1.51, 0.3, -0.4]}>
        <boxGeometry args={[0.02, 0.1, 0.3]} />
        <meshStandardMaterial color="#34d399" emissive="#34d399" emissiveIntensity={5} />
      </mesh>

      {/* Glowing Battery Core under chassis */}
      <mesh position={[0, 0.1, 0]}>
        <boxGeometry args={[2.0, 0.05, 1.0]} />
        <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={3} />
      </mesh>

      {/* Wheels */}
      <group ref={wheelsRef}>
        {/* Front Left */}
        <mesh position={[0.9, 0.15, 0.75]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.25, 32]} />
          <meshStandardMaterial color="#0f172a" roughness={0.8} />
        </mesh>
        {/* Front Right */}
        <mesh position={[0.9, 0.15, -0.75]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.25, 32]} />
          <meshStandardMaterial color="#0f172a" roughness={0.8} />
        </mesh>
        {/* Rear Left */}
        <mesh position={[-0.9, 0.15, 0.75]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.25, 32]} />
          <meshStandardMaterial color="#0f172a" roughness={0.8} />
        </mesh>
        {/* Rear Right */}
        <mesh position={[-0.9, 0.15, -0.75]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.3, 0.3, 0.25, 32]} />
          <meshStandardMaterial color="#0f172a" roughness={0.8} />
        </mesh>
      </group>
    </group>
  );
};

// Charging Station Node
const ChargingStation3D: React.FC = () => {
  return (
    <group position={[2.5, 0, 0.8]}>
      {/* Main Charger Block */}
      <mesh position={[0, 0.8, 0]} castShadow>
        <boxGeometry args={[0.5, 1.6, 0.5]} />
        <meshStandardMaterial color="#0f172a" roughness={0.2} metalness={0.8} />
      </mesh>
      {/* Emissive Charging Indicator Ring */}
      <mesh position={[0, 1.2, 0.26]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.12, 0.12, 0.02, 32]} />
        <meshStandardMaterial color="#34d399" emissive="#34d399" emissiveIntensity={4} />
      </mesh>
      {/* Glowing Energy Cable Connecting to Car */}
      <mesh position={[-1.0, 0.5, -0.2]} rotation={[0, 0, -Math.PI / 8]}>
        <cylinderGeometry args={[0.03, 0.03, 1.8, 16]} />
        <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={3} />
      </mesh>
    </group>
  );
};

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0b0f19] text-white flex flex-col justify-between overflow-x-hidden relative">
      {/* Global Background Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Header bar */}
      <header className="h-20 flex items-center justify-between px-8 md:px-16 border-b border-[#1e293b] backdrop-blur-md bg-[#0b0f19]/70 sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-8 h-8 text-cyan-400" />
          <span className="font-bold text-xl bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            ChargeRL
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="px-5 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-[#1e293b]/60 transition">
            Sign In
          </Link>
          <Link to="/register" className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:opacity-90 text-black font-semibold rounded-xl transition shadow-[0_0_20px_rgba(34,211,238,0.2)]">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-2 items-center px-8 md:px-16 py-12 gap-12 max-w-7xl mx-auto w-full">
        {/* Text Area */}
        <div className="space-y-6 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold rounded-full uppercase tracking-wider">
            <Cpu className="w-3.5 h-3.5" /> B.Tech AI/DS Project
          </div>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight">
            Charge Smarter. <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 bg-clip-text text-transparent">
              Drive Further.
            </span>
          </h1>
          <p className="text-gray-400 text-base md:text-lg leading-relaxed">
            An intelligent electric vehicle scheduling & battery management ecosystem powered by 
            <strong> Gymnasium Deep Q-Network (DQN)</strong> and <strong>PPO Reinforcement Learning</strong>.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <Link to="/register" className="px-8 py-4 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:opacity-95 text-black font-bold rounded-xl transition text-center shadow-lg shadow-cyan-500/15">
              Launch Platform
            </Link>
            <Link to="/login" className="px-8 py-4 border border-[#334155] hover:bg-[#1e293b] text-white font-bold rounded-xl transition text-center">
              Explore Demo Mode
            </Link>
          </div>

          {/* Quick specs section */}
          <div className="grid grid-cols-3 gap-6 pt-10 border-t border-[#1e293b]/60">
            <div>
              <p className="text-2xl font-bold text-cyan-400">98.4%</p>
              <p className="text-xs text-gray-500 uppercase mt-0.5 font-semibold">Cost Efficiency</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-400">-30%</p>
              <p className="text-xs text-gray-500 uppercase mt-0.5 font-semibold">Battery Degradation</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">DQN / PPO</p>
              <p className="text-xs text-gray-500 uppercase mt-0.5 font-semibold">RL Decision Engine</p>
            </div>
          </div>
        </div>

        {/* 3D Visual Panel */}
        <div className="h-[400px] sm:h-[500px] glass-panel rounded-3xl border border-[#334155]/60 overflow-hidden relative shadow-inner">
          <div className="absolute top-6 left-6 z-10 flex items-center gap-2">
            <BatteryCharging className="w-5 h-5 text-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Live 3D Telemetry Canvas</span>
          </div>

          <Canvas shadows camera={{ position: [5, 3, 5], fov: 40 }}>
            <ambientLight intensity={0.6} />
            <pointLight position={[10, 10, 10]} intensity={1.5} />
            <directionalLight
              position={[-5, 5, 5]}
              intensity={1}
              castShadow
              shadow-mapSize-width={1024}
              shadow-mapSize-height={1024}
            />
            
            <Stars radius={100} depth={50} count={300} factor={4} saturation={0} fade speed={1} />
            
            <Float speed={1.8} rotationIntensity={0.2} floatIntensity={0.4}>
              <group position={[0, -0.2, 0]}>
                <FuturisticCar />
                <ChargingStation3D />
                {/* Floor grid helper */}
                <gridHelper args={[15, 15, "#1e293b", "#0f172a"]} position={[0, 0, 0]} />
              </group>
            </Float>

            <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} maxPolarAngle={Math.PI / 2.2} />
          </Canvas>
        </div>
      </main>

      {/* Footer bar */}
      <footer className="h-16 flex items-center justify-between px-8 md:px-16 border-t border-[#1e293b]/60 text-xs text-gray-500">
        <p>© 2026 ChargeRL Hub. Developed for AI/DS Presentation.</p>
        <div className="flex gap-4">
          <span className="hover:text-white cursor-pointer">Abstract</span>
          <span className="hover:text-white cursor-pointer">Gymnasium Env</span>
          <span className="hover:text-white cursor-pointer">DQN Policy</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
