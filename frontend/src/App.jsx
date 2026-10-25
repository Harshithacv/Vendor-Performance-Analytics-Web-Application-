import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import Login from './pages/Login';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard';
import VendorAnalytics from './pages/VendorAnalytics';
import VendorDetail from './pages/VendorDetail';
import PurchaseSales from './pages/PurchaseSales';
import InventoryAnalytics from './pages/InventoryAnalytics';
import ComparisonReports from './pages/ComparisonReports';
import DataUpload from './pages/DataUpload';
import ReportsExport from './pages/ReportsExport';

function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B1120] text-slate-800 dark:text-[#F1F5F9] flex flex-col font-sans transition-colors duration-200">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-x-hidden min-h-[calc(100vh-4rem)] bg-slate-50 dark:bg-[#0B1120]">
          {children}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Dashboard />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/vendors"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <VendorAnalytics />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/vendors/:id"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <VendorDetail />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/purchases-sales"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <PurchaseSales />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/inventory"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <InventoryAnalytics />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/comparison"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ComparisonReports />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <DataUpload />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <ReportsExport />
                  </AppLayout>
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;

