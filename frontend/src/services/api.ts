import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authService = {
  register: (data: any) => api.post('/auth/register', data).then(r => r.data),
  login: (data: any) => api.post('/auth/login', data).then(r => r.data),
  getMe: () => api.get('/auth/me').then(r => r.data),
};

export const vehicleService = {
  getVehicles: () => api.get('/vehicles').then(r => r.data),
  addVehicle: (data: any) => api.post('/vehicles', data).then(r => r.data),
  getVehicleDetails: (id: number) => api.get(`/vehicles/${id}`).then(r => r.data),
  updateVehicle: (id: number, data: any) => api.put(`/vehicles/${id}`, data).then(r => r.data),
};

export const batteryService = {
  getTelemetryHistory: (vehicleId: number) => api.get(`/battery/${vehicleId}`).then(r => r.data),
  recordTelemetry: (data: any) => api.post('/battery/telemetry', data).then(r => r.data),
  getBatteryHealth: (vehicleId: number) => api.get(`/battery/${vehicleId}/health`).then(r => r.data),
  getBatteryDegradationPredict: (vehicleId: number) => api.post(`/battery/${vehicleId}/predict`).then(r => r.data),
};

export const stationService = {
  getStations: () => api.get('/stations').then(r => r.data),
  getStationDetails: (id: number) => api.get(`/stations/${id}`).then(r => r.data),
};

export const bookingService = {
  getBookings: () => api.get('/bookings').then(r => r.data),
  createBooking: (data: any) => api.post('/bookings', data).then(r => r.data),
  cancelBooking: (id: number) => api.delete(`/bookings/${id}`).then(r => r.data),
  getQueueTelemetry: (stationId: number) => api.get(`/bookings/queue/${stationId}`).then(r => r.data),
};

export const rlService = {
  getRecommendation: (data: any) => api.post('/rl/recommend', data).then(r => r.data),
  simulateState: () => api.post('/rl/simulate').then(r => r.data),
  getHistory: () => api.get('/rl/history').then(r => r.data),
};

export const analyticsService = {
  getDashboardAnalytics: () => api.get('/analytics/dashboard').then(r => r.data),
};

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const chatService = {
  sendMessage: (messages: ChatMessage[]) =>
    api.post<{ reply: string }>('/chat/message', { messages }).then(r => r.data),
};

export default api;
