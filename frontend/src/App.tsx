import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import MyEV from './pages/MyEV';
import BatteryManagement from './pages/BatteryManagement';
import FindStations from './pages/FindStations';
import SmartCharging from './pages/SmartCharging';
import LiveCharging from './pages/LiveCharging';
import Bookings from './pages/Bookings';
import HistoryPage from './pages/History';
import Analytics from './pages/Analytics';
import ChatAssistant from './pages/ChatAssistant';

// Simple Route Guard
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Private Dashboard Console Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-ev"
          element={
            <ProtectedRoute>
              <MyEV />
            </ProtectedRoute>
          }
        />
        <Route
          path="/battery"
          element={
            <ProtectedRoute>
              <BatteryManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/stations"
          element={
            <ProtectedRoute>
              <FindStations />
            </ProtectedRoute>
          }
        />
        <Route
          path="/smart-charging"
          element={
            <ProtectedRoute>
              <SmartCharging />
            </ProtectedRoute>
          }
        />
        <Route
          path="/live-charging"
          element={
            <ProtectedRoute>
              <LiveCharging />
            </ProtectedRoute>
          }
        />
        <Route
          path="/bookings"
          element={
            <ProtectedRoute>
              <Bookings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assistant"
          element={
            <ProtectedRoute>
              <ChatAssistant />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
