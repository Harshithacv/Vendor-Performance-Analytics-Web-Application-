import React, { useState, useEffect } from 'react';
import { vendorAPI, analyticsAPI } from '../services/api';
import ChartCard from '../components/ChartCard';
import { 
  GitCompare, Check, Plus, X, Award, 
  TrendingUp, Sparkles, AlertCircle, BarChart3 
} from 'lucide-react';
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, Radar, Legend, Tooltip, BarChart, Bar, XAxis, 
  YAxis, CartesianGrid, ErrorBar
} from 'recharts';

const RADAR_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'];

const ComparisonReports = () => {
  const [allVendors, setAllVendors] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch initial vendor list
  useEffect(() => {
    vendorAPI.getVendors({ page_size: 50, sort_by: 'vendor_score', sort_dir: 'desc' })
      .then((res) => {
        const vList = res.data.vendors || [];
        setAllVendors(vList);
        // Default select top 3 vendors
        if (vList.length >= 3) {
          const initialIds = [vList[0].vendor_id, vList[1].vendor_id, vList[2].vendor_id];
          setSelectedIds(initialIds);
          runComparison(initialIds);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const runComparison = (ids) => {
    if (ids.length < 2) {
      setError('Please select at least 2 vendors to compare.');
      return;
    }
    setError('');
    setLoading(true);

    analyticsAPI.compareVendors(ids)
      .then((res) => {
        setComparisonData(res.data);
      })
      .catch((err) => {
        console.error(err);
        setError('Comparison generation failed.');
      })
      .finally(() => setLoading(false));
  };

  const handleToggleVendor = (vendorId) => {
    let updated;
    if (selectedIds.includes(vendorId)) {
      if (selectedIds.length <= 2) {
        setError('At least 2 vendors must be compared.');
        return;
      }
      updated = selectedIds.filter((id) => id !== vendorId);
    } else {
      if (selectedIds.length >= 5) {
        setError('Maximum 5 vendors can be compared simultaneously.');
        return;
      }
      updated = [...selectedIds, vendorId];
    }
    setSelectedIds(updated);
    runComparison(updated);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Multi-Vendor Performance Comparison</h1>
        <p className="text-xs text-slate-500 mt-1">
          Objective benchmark evaluating delivery SLA, inventory velocity, and gross commercial profitability.
        </p>
      </div>

      {/* Vendor Selector Pill Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
          Select Vendors for Head-to-Head Comparison (2 to 5 vendors):
        </span>

        <div className="flex flex-wrap gap-2">
          {allVendors.slice(0, 15).map((v) => {
            const isSelected = selectedIds.includes(v.vendor_id);
            return (
              <button
                key={v.vendor_id}
                type="button"
                onClick={() => handleToggleVendor(v.vendor_id)}
                className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {isSelected ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5 opacity-60" />}
                <span>{v.vendor_name}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-indigo-700' : 'bg-slate-200'}`}>
                  #{v.vendor_rank}
                </span>
              </button>
            );
          })}
        </div>

        {error && (
          <p className="mt-2 text-xs text-rose-600 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{error}</span>
          </p>
        )}
      </div>

      {loading && (
        <div className="p-8 flex flex-col items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-600 border-t-transparent mb-2"></div>
          <p className="text-xs text-slate-500">Calculating head-to-head metrics...</p>
        </div>
      )}

      {comparisonData && !loading && (
        <>
          {/* Radar & Confidence Interval Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Multi-Dimensional Radar Chart */}
            <ChartCard
              title="Multi-Dimensional Competency Radar"
              subtitle="5 Core Dimensions: Spend, Margin, Turnover, Speed, SLA (0-100 scale)"
            >
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={comparisonData.radar_comparison || []}>
                    <PolarGrid stroke="#e2e8f0" />
                    <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                    {(comparisonData.selected_vendors || []).map((v, i) => (
                      <Radar
                        key={v.vendor_id}
                        name={v.vendor_name}
                        dataKey={v.vendor_name}
                        stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                        fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                        fillOpacity={0.25}
                      />
                    ))}
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>

            {/* 95% Confidence Intervals for Profit Margins */}
            <ChartCard
              title="95% Confidence Intervals for Profit Margin"
              subtitle="Statistical error bounds across compared vendor cohorts"
            >
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparisonData.confidence_intervals || []} margin={{ top: 20, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="vendor_name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={35} />
                    <YAxis unit="%" tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(val) => [`${val}%`, 'Mean Margin']}
                      contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    />
                    <Bar dataKey="margin_mean" name="Mean Profit Margin %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          </div>

          {/* Side-by-Side Head-to-Head KPI Table */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-base font-semibold text-slate-800 mb-1">Side-by-Side KPI Comparison Matrix</h3>
            <p className="text-xs text-slate-500 mb-4">Detailed metrics across selected vendors</p>

            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-xs divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase">
                  <tr>
                    <th className="py-3 px-4 w-1/4">Evaluation Metric</th>
                    {(comparisonData.selected_vendors || []).map((v) => (
                      <th key={v.vendor_id} className="py-3 px-4 text-center">
                        <div>
                          <span className="font-bold text-slate-900 block truncate">{v.vendor_name}</span>
                          <span className="text-[10px] text-indigo-600 font-medium">Rank #{v.vendor_rank}</span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {(comparisonData.head_to_head_table || []).map((row, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                      <td className="py-2.5 px-4 font-semibold text-slate-900">{row.metric}</td>
                      {(comparisonData.selected_vendors || []).map((v) => (
                        <td key={v.vendor_id} className="py-2.5 px-4 text-center font-mono font-medium">
                          {row[v.vendor_name]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Data-Backed Strategic Insights */}
          <div className="bg-gradient-to-r from-indigo-900 to-slate-900 rounded-xl p-5 text-white shadow-xs">
            <div className="flex items-center space-x-2 text-indigo-300 font-semibold text-sm mb-3">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Data-Backed Procurement Insights</span>
            </div>
            <ul className="space-y-2">
              {(comparisonData.analytical_insights || []).map((insight, idx) => (
                <li key={idx} className="flex items-start space-x-2 text-xs text-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 flex-shrink-0"></span>
                  <span className="leading-relaxed">{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default ComparisonReports;
