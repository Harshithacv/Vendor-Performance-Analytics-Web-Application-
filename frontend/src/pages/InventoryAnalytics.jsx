import React, { useState, useEffect } from 'react';
import { analyticsAPI, reportsAPI } from '../services/api';
import KPICard from '../components/KPICard';
import ChartCard from '../components/ChartCard';
import { 
  Package, DollarSign, RefreshCw, AlertTriangle, 
  Store, Download, ArrowUpRight, ArrowDownRight, Info 
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  CartesianGrid, Legend
} from 'recharts';

const InventoryAnalytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analyticsAPI.getInventory()
      .then((res) => setData(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading && !data) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent mb-2"></div>
        <p className="text-xs text-slate-500">Loading store inventory snapshots...</p>
      </div>
    );
  }

  const formatCurrency = (val) => {
    if (!val) return '$0.00';
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
    return `$${Number(val).toLocaleString()}`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inventory & Stock Analytics</h1>
          <p className="text-xs text-slate-500 mt-1">
            Store stock valuation, capital locked in unsold inventory, and vendor turnover velocity.
          </p>
        </div>
        <a
          href={reportsAPI.getExportUrl('inventory')}
          download="inventory_report.csv"
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 shadow-xs transition"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Stock Records</span>
        </a>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Beginning Valuation"
          value={formatCurrency(data?.begin_inventory_value)}
          subtext={`${Number(data?.begin_inventory_qty || 0).toLocaleString()} initial units`}
          icon={Package}
          color="indigo"
        />
        <KPICard
          title="Ending Valuation"
          value={formatCurrency(data?.end_inventory_value)}
          subtext={`${Number(data?.end_inventory_qty || 0).toLocaleString()} ending units`}
          icon={Package}
          color="emerald"
        />
        <KPICard
          title="Net Stock Change"
          value={formatCurrency(data?.net_inventory_change_value)}
          subtext={data?.net_inventory_change_value >= 0 ? "Inventory expanded" : "Inventory depleted"}
          icon={RefreshCw}
          color="blue"
        />
        <KPICard
          title="Capital Locked in Stock"
          value={formatCurrency(data?.capital_locked_in_unsold_stock)}
          subtext="Unsold ending valuation"
          icon={DollarSign}
          color="amber"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Store Distribution */}
        <ChartCard
          title="Inventory Valuation Across Retail Stores"
          subtitle="Stock dollars distributed by store location"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.store_inventory_distribution || []} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="city" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={35} />
                <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Valuation']}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        {/* Inventory Turnover by Vendor */}
        <ChartCard
          title="Vendor Inventory Turnover Velocity"
          subtitle="Sales quantity relative to procurement quantity"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.inventory_turnover_by_vendor || []} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="vendor_name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={35} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`${val}x`, 'Turnover Ratio']}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="turnover_ratio" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      {/* Excess Stock & Slow Moving Warnings */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 mb-3">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <div>
            <h3 className="text-base font-semibold text-slate-800">Excess Stock & Slow-Moving Inventory Identification</h3>
            <p className="text-xs text-slate-500">Suppliers with turnover ratio &lt; 0.6x representing excess capital tie-up</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(data?.top_excess_inventory_vendors || []).map((v, i) => (
            <div key={i} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 text-xs">
              <span className="font-semibold text-slate-900 block truncate">{v.vendor_name}</span>
              <div className="mt-2 flex items-center justify-between text-slate-600">
                <span>Turnover Ratio:</span>
                <span className="font-bold text-amber-600 font-mono">{v.turnover_ratio}x</span>
              </div>
              <div className="mt-1 flex items-center justify-between text-slate-500 text-[11px]">
                <span>Purchased: {v.purchase_qty?.toLocaleString()}</span>
                <span>Sold: {v.sales_qty?.toLocaleString()}</span>
              </div>
              <span className="mt-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">
                {v.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Inventory Records Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-base font-semibold text-slate-800 mb-1">Recent Inventory Snapshot Records</h3>
        <p className="text-xs text-slate-500 mb-4">Stock on hand counts logged across retail branches</p>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs divide-y divide-slate-100">
            <thead>
              <tr className="text-slate-400 font-semibold uppercase">
                <th className="py-2.5 px-3">Inventory ID</th>
                <th className="py-2.5 px-3">Store Location</th>
                <th className="py-2.5 px-3">Brand / Item</th>
                <th className="py-2.5 px-3 text-right">On Hand</th>
                <th className="py-2.5 px-3 text-right">Unit Price</th>
                <th className="py-2.5 px-3 text-right">Inventory Value</th>
                <th className="py-2.5 px-3 text-center">Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 text-slate-700">
              {(data?.recent_inventory_records || []).map((r, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-mono text-slate-500">{r.inventory_code}</td>
                  <td className="py-2.5 px-3 font-medium text-slate-800">{r.city} (Store #{r.store})</td>
                  <td className="py-2.5 px-3 truncate max-w-[180px]">{r.item_name}</td>
                  <td className="py-2.5 px-3 text-right font-semibold">{r.on_hand}</td>
                  <td className="py-2.5 px-3 text-right font-mono">${r.price.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-slate-900">${(r.on_hand * r.price).toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      r.snapshot_type === 'BEGIN' ? 'bg-blue-50 text-blue-700' : 'bg-emerald-50 text-emerald-700'
                    }`}>
                      {r.snapshot_type}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default InventoryAnalytics;
