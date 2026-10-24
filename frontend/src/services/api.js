import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vpa_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  signup: (name, email, password) => api.post('/auth/signup', { name, email, password }),
  getMe: () => api.get('/auth/me'),
};

export const dashboardAPI = {
  getSummary: (params) => api.get('/dashboard/summary', { params }),
};

export const vendorAPI = {
  getVendors: (params) => api.get('/vendors', { params }),
  getVendorDetail: (vendorId) => api.get(`/vendors/${vendorId}`),
  addVendor: (data) => api.post('/vendors', data),
};

export const analyticsAPI = {
  getPurchasing: (params) => api.get('/analytics/purchasing', { params }),
  getSales: (params) => api.get('/analytics/sales', { params }),
  getInventory: (params) => api.get('/analytics/inventory', { params }),
  getPerformanceRanking: (params) => api.get('/analytics/vendor-performance', { params }),
  compareVendors: (vendorIds) => api.post('/analytics/vendor-comparison', { vendor_ids: vendorIds }),
  compareVendorsGet: (vendorIdsStr) => api.get('/analytics/vendor-comparison', { params: { vendor_ids: vendorIdsStr } }),
};

export const uploadAPI = {
  uploadFile: (formData) => api.post('/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getPreview: (uploadId) => api.get(`/uploads/${uploadId}/preview`),
  confirmUpload: (uploadId) => api.post(`/uploads/${uploadId}/confirm`),
  getHistory: () => api.get('/uploads/history'),
};

export const reportsAPI = {
  getExportUrl: (reportType, vendorId) => {
    let url = `/api/reports/export?report_type=${reportType}&format=csv`;
    if (vendorId) url += `&vendor_id=${vendorId}`;
    return url;
  },
};

export default api;
