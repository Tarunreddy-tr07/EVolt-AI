import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Car, Battery, MapPin, BrainCircuit, Activity,
  CalendarDays, History, BarChart3, Bell, User, Settings, LogOut, Menu, X, MessageCircle
} from 'lucide-react';
import { authService, vehicleService } from '../services/api';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [profile, setProfile] = useState<any>(null);
  const [activeEV, setActiveEV] = useState<any>(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: 1, title: 'Charging recommendation ready', message: 'Your RL agent has a new charging recommendation.', unread: true },
    { id: 2, title: 'Battery status stable', message: 'Your latest battery telemetry is within the healthy range.', unread: true },
  ]);
  const navigate = useNavigate();
  const location = useLocation();
  const unreadCount = notifications.filter((notification) => notification.unread).length;

  useEffect(() => {
    // Fetch profile and active EV details
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    authService.getMe()
      .then((user) => {
        setProfile(user);
        return vehicleService.getVehicles();
      })
      .then((vehicles) => {
        if (vehicles && vehicles.length > 0) {
          setActiveEV(vehicles[0]);
        }
      })
      .catch(() => {
        localStorage.removeItem('token');
        navigate('/login');
      });
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const markNotificationsRead = () => {
    setNotifications((current) => current.map((notification) => ({ ...notification, unread: false })));
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'My EV', path: '/my-ev', icon: Car },
    { name: 'Battery Health', path: '/battery', icon: Battery },
    { name: 'Find Stations', path: '/stations', icon: MapPin },
    { name: 'Smart Charging', path: '/smart-charging', icon: BrainCircuit },
    { name: 'Live Charging', path: '/live-charging', icon: Activity },
    { name: 'Bookings', path: '/bookings', icon: CalendarDays },
    { name: 'Charging History', path: '/history', icon: History },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'EV Assistant', path: '/assistant', icon: MessageCircle },
  ];

  return (
    <div className="min-h-screen bg-[#0b0f19] text-white flex">
      {/* Sidebar - Desktop */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } bg-[#0f172a] border-r border-[#1e293b] flex flex-col justify-between transition-all duration-300 z-30 hidden md:flex`}
      >
        <div>
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-[#1e293b]">
            <Link to="/" className="flex items-center gap-2">
              <BrainCircuit className="w-8 h-8 text-cyan-400" />
              {sidebarOpen && <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">ChargeRL</span>}
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-150 ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-400 border-l-4 border-cyan-400 font-semibold'
                      : 'text-gray-400 hover:bg-[#1e293b] hover:text-white'
                  }`}
                  title={item.name}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {sidebarOpen && <span>{item.name}</span>}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User profile / Logout */}
        <div className="p-4 border-t border-[#1e293b] space-y-2">
          {sidebarOpen && profile && (
            <div className="flex items-center gap-3 px-3 py-2 bg-[#1e293b]/40 rounded-xl mb-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-emerald-500 flex items-center justify-center font-bold text-white uppercase">
                {profile.name[0]}
              </div>
              <div className="overflow-hidden">
                <p className="font-medium text-sm truncate">{profile.name}</p>
                <p className="text-xs text-gray-400 truncate">{profile.role}</p>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-4 px-4 py-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-all font-medium"
            title="Sign Out"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navigation Header */}
        <header className="h-16 bg-[#0f172a] border-b border-[#1e293b] flex items-center justify-between px-6 z-20">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-400 hover:text-white hidden md:block"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="text-gray-300 text-sm hidden sm:flex items-center gap-2">
              {activeEV ? (
                <>
                  <Car className="w-4 h-4 text-cyan-400 animate-pulse" />
                  <span>Active EV: <strong className="text-white">{activeEV.vehicle_model}</strong></span>
                  <span className="bg-[#1e293b] px-2 py-0.5 rounded-full text-xs text-emerald-400 font-semibold border border-[#334155]">
                    {activeEV.current_soc}% SoC
                  </span>
                </>
              ) : (
                <span>No vehicle registered</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications */}
            <div className="relative">
              <button
                type="button"
                aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
                aria-expanded={notificationsOpen}
                onClick={() => setNotificationsOpen((open) => !open)}
                className="relative text-gray-400 hover:text-white transition"
              >
                <Bell className="w-6 h-6" />
              </button>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-cyan-500 text-black font-extrabold text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
              {notificationsOpen && (
                <div className="absolute right-0 top-10 z-40 w-80 overflow-hidden rounded-xl border border-[#334155] bg-[#111827] shadow-2xl">
                  <div className="flex items-center justify-between border-b border-[#334155] px-4 py-3">
                    <h2 className="text-sm font-semibold text-white">Notifications</h2>
                    <button
                      type="button"
                      onClick={markNotificationsRead}
                      disabled={unreadCount === 0}
                      className="text-xs text-cyan-400 hover:text-cyan-300 disabled:text-gray-500"
                    >
                      Mark all read
                    </button>
                  </div>
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`border-b border-[#1e293b] px-4 py-3 last:border-b-0 ${
                          notification.unread ? 'bg-cyan-500/5' : ''
                        }`}
                      >
                        <div className="flex gap-2">
                          {notification.unread && <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-cyan-400" />}
                          <div>
                            <p className="text-sm font-medium text-gray-200">{notification.title}</p>
                            <p className="mt-1 text-xs leading-relaxed text-gray-400">{notification.message}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="px-4 py-6 text-center text-sm text-gray-400">You’re all caught up.</p>
                  )}
                </div>
              )}
            </div>

            {/* Profile Avatar */}
            {profile && (
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-300 hidden md:block">{profile.name}</span>
                <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400 flex items-center justify-center font-bold text-cyan-400 uppercase">
                  {profile.name[0]}
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#0b0f19]">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
