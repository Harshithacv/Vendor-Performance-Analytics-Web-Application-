import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { vendorAPI } from '../services/api';
import ChartCard from '../components/ChartCard';
import KPICard from '../components/KPICard';
import { 
  ArrowLeft, Award, Clock, DollarSign, TrendingUp, Package, 
  CheckCircle, Truck, AlertCircle 
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  CartesianGrid, LineChart, Line
} from 'recharts';

const VendorDetail = () => {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    vendorAPI.getVendorDetail(id)
      .then((res) => {
        setData(res.data);
        setError('');
      })
      .catch((err) => {
        console.error(err);
        setError('Failed to load vendor details');
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent mb-2"></div>
        <p className="text-xs text-slate-500">Loading vendor scorecard...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center">
        <p className="text-rose-600 text-sm font-semibold">{error || 'Vendor not found'}</p>
        <Link to="/vendors" className="mt-4 inline-flex items-center space-x-1 text-xs text-indigo-600 font-semibold">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Directory</span>
        </Link>
      </div>
    );
  }

  const { metrics, purchase_history, monthly_trends, top_brands } = data;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link to="/vendors" className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition mb-3">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Vendor Directory</span>
        </Link>

        {/* Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">{data.vendor_name}</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                Rank #{metrics.vendor_rank}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Vendor Code: <span className="font-mono text-slate-700 font-semibold">{data.vendor_number}</span> &bull; Category: {data.category}
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-indigo-50 border border-indigo-100 px-4 py-2.5 rounded-xl">
            <Award className="w-6 h-6 text-indigo-600" />
            <div>
              <span className="text-[11px] font-semibold text-indigo-600 uppercase tracking-wider block">CVPI Score</span>
              <span className="text-xl font-black text-indigo-950">{metrics.vendor_score.toFixed(1)} / 100</span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Procurement Spend"
          value={`$${metrics.total_purchase_dollars.toLocaleString()}`}
          subtext={`${metrics.total_orders} Total Orders Placed`}
          icon={DollarSign}
          color="indigo"
        />
        <KPICard
          title="Downstream Revenue"
          value={`$${metrics.total_sales_dollars.toLocaleString()}`}
          subtext={`Margin: ${metrics.profit_margin.toFixed(1)}%`}
          icon={TrendingUp}
          color="emerald"
        />
        <KPICard
          title="Average Lead Time"
          value={`${metrics.avg_delivery_days.toFixed(1)} Days`}
          subtext={`On-Time Rate: ${metrics.on_time_delivery_rate.toFixed(1)}%`}
          icon={Clock}
          color="blue"
        />
        <KPICard
          title="Stock Turnover Ratio"
          value={`${metrics.stock_turnover.toFixed(2)}x`}
          subtext={`Freight: $${metrics.freight_cost.toLocaleString()} (${metrics.freight_percentage.toFixed(2)}%)`}
          icon={Truck}
          color="purple"
        />
      </div>

      {/* Charts: Monthly Trend & Top Brands */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Procurement Spend Trend"
          subtitle="Monthly purchase amounts for this vendor"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthly_trends || []} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Spend']}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Line type="monotone" dataKey="spend" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard
          title="Top Brands Supplied"
          subtitle="Highest procurement volume items"
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={top_brands || []} layout="vertical" margin={{ top: 5, right: 20, left: 50, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
                <XAxis type="number" tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
                <YAxis dataKey="description" type="category" width={100} tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(val) => [`$${Number(val).toLocaleString()}`, 'Purchased']}
                  contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Bar dataKey="dollars" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      {/* Purchase Orders Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-base font-semibold text-slate-800 mb-1">Purchase Order History</h3>
        <p className="text-xs text-slate-500 mb-4">Historical orders recorded for {data.vendor_name}</p>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">PO Number</th>
                <th className="py-2.5 px-3">PO Date</th>
                <th className="py-2.5 px-3">Invoice Date</th>
                <th className="py-2.5 px-3 text-right">Quantity</th>
                <th className="py-2.5 px-3 text-right">Freight</th>
                <th className="py-2.5 px-3 text-right">Total Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {(purchase_history || []).map((po, idx) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-mono font-medium text-indigo-600">#{po.po_number}</td>
                  <td className="py-2.5 px-3 text-slate-500">{po.po_date}</td>
                  <td className="py-2.5 px-3 text-slate-500">{po.invoice_date}</td>
                  <td className="py-2.5 px-3 text-right">{po.quantity.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-right text-slate-500">${po.freight.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-right font-semibold text-slate-900">${po.dollars.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default VendorDetail;
