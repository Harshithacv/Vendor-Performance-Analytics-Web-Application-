import React, { useState, useEffect } from 'react';
import { analyticsAPI, reportsAPI } from '../services/api';
import KPICard from '../components/KPICard';
import ChartCard from '../components/ChartCard';
import FilterBar from '../components/FilterBar';
import { 
  DollarSign, ShoppingBag, TrendingUp, Download, 
  Layers, PieChart as PieIcon, ArrowUpDown, Sparkles 
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  CartesianGrid, LineChart, Line, Legend, AreaChart, Area
} from 'recharts';

const PurchaseSales = () => {
  const [purchasing, setPurchasing] = useState(null);
  const [sales, setSales] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    setLoading(true);
    Promise.all([
      analyticsAPI.getPurchasing(filters),
      analyticsAPI.getSales(filters),
    ])
      .then(([pRes, sRes]) => {
        setPurchasing(pRes.data);
        setSales(sRes.data);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [filters]);

  if (loading && (!purchasing || !sales)) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent mb-2"></div>
        <p className="text-xs text-slate-500">Computing procurement and sales analytics...</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Purchase & Sales Analytics</h1>
          <p className="text-xs text-slate-500 mt-1">
            Commercial procurement economics, bulk pricing elasticity, and sales conversion rates.
          </p>
        </div>
        <a
          href={reportsAPI.getExportUrl('purchases', filters.vendor_id)}
          download="purchase_transactions.csv"
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 shadow-xs transition"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Transactions</span>
        </a>
      </div>

      <FilterBar onFilterChange={setFilters} showCategory={false} />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Procurement Spend"
          value={`$${Number(purchasing?.total_spend || 0).toLocaleString()}`}
          subtext={`${purchasing?.total_orders || 0} Purchase Orders Placed`}
          icon={DollarSign}
          color="indigo"
        />
        <KPICard
          title="Downstream Revenue"
          value={`$${Number(sales?.total_sales_dollars || 0).toLocaleString()}`}
          subtext={`Gross Profit: $${Number(sales?.gross_profit || 0).toLocaleString()}`}
          icon={TrendingUp}
          color="emerald"
        />
        <KPICard
          title="Average Order Value"
          value={`$${Number(purchasing?.avg_order_value || 0).toLocaleString()}`}
          subtext={`Avg Unit Cost: $${Number(purchasing?.avg_unit_price || 0).toFixed(2)}`}
          icon={ShoppingBag}
          color="blue"
        />
        <KPICard
          title="Commercial Margin"
          value={`${Number(sales?.avg_profit_margin || 0).toFixed(1)}%`}
          subtext="Net gross profit percentage"
          icon={Layers}
          color="purple"
        />
      </div>

      {/* Bulk Purchasing Tiers & Pareto Concentration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bulk Purchasing Tiers Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-3 border-b border-slate-100 mb-3">
            <h3 className="text-base font-semibold text-slate-800">Impact of Bulk Purchasing on Unit Price</h3>
            <p className="text-xs text-slate-500">Order size tiers vs unit purchase cost (Economies of Scale)</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs divide-y divide-slate-100">
              <thead>
                <tr className="text-slate-400 font-semibold uppercase">
                  <th className="py-2.5">Order Tier</th>
                  <th className="py-2.5 text-right">Orders Placed</th>
                  <th className="py-2.5 text-right">Avg Unit Cost</th>
                  <th className="py-2.5 text-right">Total Spend</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-slate-700">
                {(purchasing?.bulk_purchasing_tiers || []).map((t, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-3 font-semibold text-slate-800">{t.tier}</td>
                    <td className="py-3 text-right">{t.orders.toLocaleString()}</td>
                    <td className="py-3 text-right font-mono font-bold text-indigo-600">${t.avg_unit_price.toFixed(2)}</td>
                    <td className="py-3 text-right font-medium">${t.total_spend.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 p-3 rounded-lg bg-emerald-50 border border-emerald-100 text-xs text-emerald-800">
            <span className="font-semibold">Insight: </span>
            Large bulk orders achieve significant unit cost savings compared to small purchase sizes.
          </div>
        </div>

        {/* Pareto Procurement Dependency Chart */}
        <ChartCard
          title="Procurement Concentration (Pareto 80/20)"
          subtitle="Cumulative percentage of total spend across top suppliers"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={purchasing?.pareto_procurement || []} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="vendor_name" tick={{ fontSize: 9 }} interval={0} angle={-20} textAnchor="end" height={45} />
                <YAxis unit="%" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`${val}%`, 'Cumulative Spend']}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="cumulative_percentage" stroke="#6366f1" fill="#e0e7ff" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      {/* Sales vs Purchases Comparison */}
      <ChartCard
        title="Sales Revenue vs Purchase Spend Comparison"
        subtitle="Downstream commercial margin generation per vendor"
      >
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sales?.sales_vs_purchases || []} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="vendor_name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={40} />
              <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(val) => [`$${Number(val).toLocaleString()}`]}
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="purchases" name="Procurement Spend" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="sales" name="Sales Revenue" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>

      {/* Pricing Opportunities & Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pricing Adjustment Opportunities */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-100 mb-3">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <div>
              <h3 className="text-base font-semibold text-slate-800">Pricing & Promotion Opportunities</h3>
              <p className="text-xs text-slate-500">Brands with high margins but lower sales velocity</p>
            </div>
          </div>

          <div className="space-y-3">
            {(sales?.pricing_adjustment_opportunities || []).map((opp, idx) => (
              <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-900">{opp.description}</span>
                  <span className="font-bold text-indigo-600">${opp.avg_price.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-slate-500">
                  <span>Sold: {opp.sales_qty} units (${opp.sales_dollars.toLocaleString()})</span>
                  <span className="text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-sm">Price Promotion Opportunity</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Purchase Transactions Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="pb-3 border-b border-slate-100 mb-3">
            <h3 className="text-base font-semibold text-slate-800">Recent Transaction Line Items</h3>
            <p className="text-xs text-slate-500">Latest procurement line records</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs divide-y divide-slate-100">
              <thead>
                <tr className="text-slate-400 font-semibold uppercase">
                  <th className="py-2">Item</th>
                  <th className="py-2 text-right">Qty</th>
                  <th className="py-2 text-right">Unit Price</th>
                  <th className="py-2 text-right">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-slate-700">
                {(purchasing?.recent_transactions || []).slice(0, 6).map((tx, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="py-2.5 font-medium text-slate-800 truncate max-w-[150px]">{tx.description}</td>
                    <td className="py-2.5 text-right">{tx.quantity}</td>
                    <td className="py-2.5 text-right font-mono">${tx.unit_price.toFixed(2)}</td>
                    <td className="py-2.5 text-right font-semibold text-slate-900">${tx.total_amount.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PurchaseSales;
