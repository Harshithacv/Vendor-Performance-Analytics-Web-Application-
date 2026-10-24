import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { dashboardAPI } from '../services/api';
import KPICard from '../components/KPICard';
import ChartCard from '../components/ChartCard';
import FilterBar from '../components/FilterBar';
import { 
  Users, DollarSign, TrendingUp, Clock, CheckCircle2, 
  Package, AlertTriangle, ArrowRight, ShieldAlert, Info 
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  CartesianGrid, PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';

const COLORS = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({});

  const fetchData = (filterParams = {}) => {
    setLoading(true);
    dashboardAPI.getSummary(filterParams)
      .then((res) => {
        setData(res.data);
        setError('');
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to fetch dashboard summary from backend API');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData(filters);
  }, [filters]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const formatCurrency = (val) => {
    if (val === undefined || val === null) return '$0.00';
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
    return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading && !data) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-10 w-10 border-3 border-indigo-600 border-t-transparent mb-3"></div>
        <p className="text-sm text-slate-500 font-medium">Aggregating live metrics from MySQL...</p>
      </div>
    );
  }

  const kpis = data?.kpis || {};

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Executive Vendor Dashboard</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time procurement performance, commercial margins, and fulfillment SLAs.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Link
            to="/comparison"
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 shadow-xs transition"
          >
            Compare Vendors
          </Link>
          <Link
            to="/reports"
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition"
          >
            Export Report
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar onFilterChange={handleFilterChange} />

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Vendors"
          value={kpis.total_vendors || 0}
          subtext="Active in catalog"
          icon={Users}
          color="indigo"
        />
        <KPICard
          title="Procurement Spend"
          value={formatCurrency(kpis.total_procurement_spend)}
          subtext={`${kpis.total_purchase_orders || 0} Total Purchase Orders`}
          icon={DollarSign}
          color="blue"
        />
        <KPICard
          title="Downstream Sales"
          value={formatCurrency(kpis.total_sales_revenue)}
          subtext={`Avg Margin: ${kpis.average_profit_margin || 0}%`}
          icon={TrendingUp}
          color="emerald"
        />
        <KPICard
          title="Avg Delivery Lead Time"
          value={`${kpis.average_delivery_days || 0} Days`}
          subtext={`On-Time Rate: ${kpis.on_time_delivery_rate || 0}%`}
          icon={Clock}
          color="purple"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Vendors by Spend Bar Chart */}
        <div className="lg:col-span-2">
          <ChartCard
            title="Top Vendors by Procurement Spend"
            subtitle="Procurement dollar allocation across major supply partners"
            headerRight={
              <Link to="/vendors" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 inline-flex items-center space-x-1">
                <span>View Directory</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            }
          >
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.top_vendors_by_spend || []} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e2e8f0" />
                  <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} textAnchor="middle" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="vendor_name" type="category" width={110} tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Spend']}
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="spend" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>

        {/* Spend by Category Pie Chart */}
        <div>
          <ChartCard
            title="Spend by Category"
            subtitle="Product classification breakdown"
          >
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data?.spend_by_category || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="spend"
                    nameKey="category"
                  >
                    {(data?.spend_by_category || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Spend']}
                    contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>
      </div>

      {/* Monthly Procurement Trend */}
      <ChartCard
        title="Monthly Procurement Spend Trend"
        subtitle="Purchase volume and dollar trajectory over time"
      >
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data?.monthly_procurement_trend || []} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis yAxisId="left" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(val, name) => [name === 'spend' ? `$${Number(val).toLocaleString()}` : val, name === 'spend' ? 'Spend ($)' : 'PO Count']}
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Line yAxisId="left" type="monotone" dataKey="spend" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} name="Spend ($)" />
              <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} name="PO Count" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      {/* Two Column: Recent POs & Inventory Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Purchase Orders Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
            <div>
              <h3 className="text-base font-semibold text-slate-800">Recent Purchase Orders</h3>
              <p className="text-xs text-slate-500">Latest PO logs recorded in database</p>
            </div>
            <Link to="/purchases-sales" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500">
              View All
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs divide-y divide-slate-100">
              <thead>
                <tr className="text-slate-400 font-semibold uppercase">
                  <th className="py-2">PO #</th>
                  <th className="py-2">Vendor</th>
                  <th className="py-2">Date</th>
                  <th className="py-2 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-slate-700">
                {(data?.recent_purchase_orders || []).map((po, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-2.5 font-mono text-slate-500 font-medium">#{po.po_number}</td>
                    <td className="py-2.5 font-medium text-slate-800 truncate max-w-[150px]">{po.vendor_name}</td>
                    <td className="py-2.5 text-slate-500">{po.po_date}</td>
                    <td className="py-2.5 text-right font-semibold text-slate-900">${po.amount.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Inventory Snapshot Summary Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="text-base font-semibold text-slate-800">Inventory Stock Snapshot</h3>
                <p className="text-xs text-slate-500">Beginning vs Ending retail inventory status</p>
              </div>
              <Link to="/inventory" className="text-xs font-semibold text-indigo-600 hover:text-indigo-500">
                Inspect Stock
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[11px] font-semibold uppercase text-slate-500">Beginning Valuation</span>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {formatCurrency(data?.inventory_snapshot_summary?.begin_inventory_value)}
                </p>
                <span className="text-xs text-slate-500">
                  {Number(data?.inventory_snapshot_summary?.begin_inventory_qty || 0).toLocaleString()} units on hand
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-[11px] font-semibold uppercase text-slate-500">Ending Valuation</span>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {formatCurrency(data?.inventory_snapshot_summary?.end_inventory_value)}
                </p>
                <span className="text-xs text-slate-500">
                  {Number(data?.inventory_snapshot_summary?.end_inventory_qty || 0).toLocaleString()} units on hand
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-900">
              <span className="font-semibold">Net Capital Trajectory: </span>
              {data?.inventory_snapshot_summary?.net_change_value >= 0 ? (
                <span>
                  Net inventory expanded by <span className="font-bold text-emerald-700">+{formatCurrency(data?.inventory_snapshot_summary?.net_change_value)}</span> indicating healthy buffer replenishment.
                </span>
              ) : (
                <span>
                  Inventory shrank by <span className="font-bold text-amber-700">{formatCurrency(Math.abs(data?.inventory_snapshot_summary?.net_change_value))}</span> reflecting strong downstream demand sales.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Data Quality & System Alerts */}
      <div className="bg-slate-900 text-slate-100 rounded-xl p-5 shadow-xs">
        <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-3">
          <ShieldAlert className="w-4 h-4" />
          <span>Data Quality & Integrity Notes</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(data?.data_quality_notices || []).map((notice, idx) => (
            <div key={idx} className="bg-slate-800/80 border border-slate-700/60 rounded-lg p-3 text-xs">
              <span className="font-semibold text-slate-200 block mb-1">{notice.title}</span>
              <p className="text-slate-400 leading-relaxed">{notice.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
