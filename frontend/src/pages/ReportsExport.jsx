import React, { useState, useEffect } from 'react';
import { vendorAPI, reportsAPI } from '../services/api';
import { FileSpreadsheet, Download, CheckCircle, FileText, Filter } from 'lucide-react';

const ReportsExport = () => {
  const [reportType, setReportType] = useState('vendors');
  const [selectedVendor, setSelectedVendor] = useState('');
  const [vendors, setVendors] = useState([]);

  useEffect(() => {
    vendorAPI.getVendors({ page_size: 100 })
      .then((res) => setVendors(res.data.vendors || []))
      .catch((err) => console.error(err));
  }, []);

  const reportDescriptions = {
    vendors: "Complete master vendor scorecard: Composite CVPI Score, Rank, Spend, Revenue, Gross Margin %, Stock Turnover, Average Lead Time, and SLA delivery compliance.",
    purchases: "Transaction-level procurement line items: PO Number, Order Date, Actual Delivery Date, Brand, Description, Quantity, Unit Price, and Total Amount.",
    inventory: "Retail store inventory snapshots: Beginning & Ending on-hand units, item valuations, store locations, and net stock changes.",
    invoices: "Purchase order invoice logs: Invoice dates, PO schedule, Freight costs, Approval status, and Total Dollars."
  };

  const exportUrl = reportsAPI.getExportUrl(reportType, selectedVendor ? Number(selectedVendor) : undefined);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Custom Reports & Data Export</h1>
        <p className="text-xs text-slate-500 mt-1">
          Generate filtered, verified CSV extracts directly from the live MySQL database.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs max-w-2xl">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Select Report Dataset
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'vendors', label: 'Vendor Performance Scorecard' },
                { id: 'purchases', label: 'Purchases Transactions' },
                { id: 'inventory', label: 'Inventory Stock Records' },
                { id: 'invoices', label: 'Vendor Invoices & Freight' },
              ].map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setReportType(r.id)}
                  className={`p-3 text-left rounded-xl border text-xs font-semibold transition ${
                    reportType === r.id
                      ? 'border-indigo-600 bg-indigo-50/60 text-indigo-950'
                      : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <FileSpreadsheet className={`w-4 h-4 ${reportType === r.id ? 'text-indigo-600' : 'text-slate-400'}`} />
                    <span>{r.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 leading-relaxed">
            <span className="font-semibold text-slate-800">Report Scope: </span>
            {reportDescriptions[reportType]}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Filter by Vendor (Optional)
            </label>
            <select
              value={selectedVendor}
              onChange={(e) => setSelectedVendor(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white"
            >
              <option value="">All Vendors</option>
              {vendors.map((v) => (
                <option key={v.vendor_id} value={v.vendor_id}>
                  {v.vendor_name} (#{v.vendor_number})
                </option>
              ))}
            </select>
          </div>

          <div className="pt-2">
            <a
              href={exportUrl}
              download={`${reportType}_report.csv`}
              className="w-full py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/20 transition flex items-center justify-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Live CSV Report</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsExport;
