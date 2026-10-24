import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { vendorAPI, reportsAPI } from '../services/api';
import DataTable from '../components/DataTable';
import FilterBar from '../components/FilterBar';
import { Award, Download, ExternalLink, Sparkles, TrendingUp, CheckCircle, Clock } from 'lucide-react';

const VendorAnalytics = () => {
  const [vendors, setVendors] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [sortBy, setSortBy] = useState('vendor_score');
  const [sortDir, setSortDir] = useState('desc');
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchVendors = () => {
    setLoading(true);
    const params = {
      page,
      page_size: pageSize,
      sort_by: sortBy,
      sort_dir: sortDir,
      ...filters,
    };

    vendorAPI.getVendors(params)
      .then((res) => {
        setVendors(res.data.vendors);
        setTotalCount(res.data.total_count);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVendors();
  }, [page, pageSize, sortBy, sortDir, filters]);

  const handleSort = (columnKey) => {
    if (sortBy === columnKey) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(columnKey);
      setSortDir('desc');
    }
  };

  const columns = [
    {
      key: 'vendor_rank',
      label: 'Rank',
      sortable: true,
      render: (val) => (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
          val === 1 ? 'bg-amber-100 text-amber-800 border border-amber-300' :
          val <= 3 ? 'bg-indigo-100 text-indigo-800' :
          'bg-slate-100 text-slate-700'
        }`}>
          #{val}
        </span>
      ),
    },
    {
      key: 'vendor_name',
      label: 'Vendor Name',
      sortable: true,
      render: (val, row) => (
        <div>
          <Link to={`/vendors/${row.vendor_id}`} className="font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1">
            <span>{val}</span>
            <ExternalLink className="w-3 h-3 opacity-60" />
          </Link>
          <span className="text-[11px] text-slate-400 font-mono">ID #{row.vendor_number}</span>
        </div>
      ),
    },
    {
      key: 'vendor_score',
      label: 'CVPI Score',
      sortable: true,
      align: 'center',
      render: (val) => (
        <div className="flex flex-col items-center">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-md ${
            val >= 50 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
            val >= 35 ? 'bg-blue-50 text-blue-700 border border-blue-200' :
            'bg-slate-50 text-slate-700 border border-slate-200'
          }`}>
            {val.toFixed(1)} / 100
          </span>
        </div>
      ),
    },
    {
      key: 'total_purchase_dollars',
      label: 'Procurement Spend',
      sortable: true,
      align: 'right',
      render: (val) => (
        <span className="font-semibold text-slate-900">${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
      ),
    },
    {
      key: 'total_sales_dollars',
      label: 'Sales Revenue',
      sortable: true,
      align: 'right',
      render: (val) => (
        <span className="font-medium text-slate-700">${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
      ),
    },
    {
      key: 'profit_margin',
      label: 'Margin %',
      sortable: true,
      align: 'right',
      render: (val) => (
        <span className={`text-xs font-bold ${val > 0 ? 'text-emerald-600' : 'text-slate-500'}`}>
          {val.toFixed(1)}%
        </span>
      ),
    },
    {
      key: 'stock_turnover',
      label: 'Turnover',
      sortable: true,
      align: 'center',
      render: (val) => (
        <span className="text-xs font-mono font-medium text-slate-600">{val.toFixed(2)}x</span>
      ),
    },
    {
      key: 'avg_delivery_days',
      label: 'Avg Lead Time',
      sortable: true,
      align: 'center',
      render: (val) => (
        <span className="text-xs font-medium text-slate-600 flex items-center justify-center space-x-1">
          <Clock className="w-3 h-3 text-slate-400" />
          <span>{val.toFixed(1)}d</span>
        </span>
      ),
    },
    {
      key: 'on_time_delivery_rate',
      label: 'On-Time SLA',
      sortable: true,
      align: 'center',
      render: (val) => (
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
          val >= 90 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
        }`}>
          {val.toFixed(1)}%
        </span>
      ),
    },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Vendor Directory & Performance Ranking</h1>
          <p className="text-xs text-slate-500 mt-1">
            Empirical Composite Vendor Performance Index (CVPI) derived from real transactions in MySQL.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={reportsAPI.getExportUrl('vendors')}
            download="vendors_report.csv"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 shadow-xs transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
          <Link
            to="/comparison"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Comparison</span>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar onFilterChange={(newF) => { setFilters(newF); setPage(1); }} />

      {/* Table */}
      <DataTable
        columns={columns}
        data={vendors}
        totalCount={totalCount}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onSort={handleSort}
        sortBy={sortBy}
        sortDir={sortDir}
        loading={loading}
      />
    </div>
  );
};

export default VendorAnalytics;
