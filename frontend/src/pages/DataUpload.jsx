import React, { useState, useEffect } from 'react';
import { uploadAPI } from '../services/api';
import { 
  UploadCloud, FileSpreadsheet, CheckCircle2, AlertTriangle, 
  XCircle, ArrowRight, Download, RefreshCw, FileText, Check 
} from 'lucide-react';

const DataUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [uploadHistory, setUploadHistory] = useState([]);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const fetchHistory = () => {
    uploadAPI.getHistory()
      .then((res) => setUploadHistory(res.data))
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreview(null);
      setSuccessMessage('');
      setErrorMessage('');
    }
  };

  const handleValidatePreview = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a file to upload first.');
      return;
    }

    setUploading(true);
    setErrorMessage('');
    setSuccessMessage('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await uploadAPI.uploadFile(formData);
      setPreview(res.data);
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Failed to inspect and validate file.');
    } finally {
      setUploading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!preview?.upload_id) return;
    setConfirming(true);
    setErrorMessage('');

    try {
      const res = await uploadAPI.confirmUpload(preview.upload_id);
      setSuccessMessage(res.data.message || 'Dataset cleaned and successfully stored in MySQL!');
      setPreview(null);
      setSelectedFile(null);
      fetchHistory();
    } catch (err) {
      setErrorMessage(err.response?.data?.detail || 'Import failed.');
    } finally {
      setConfirming(false);
    }
  };

  const downloadSampleTemplate = () => {
    const sampleCSV = `VendorNumber,VendorName,InvoiceDate,PONumber,PODate,PayDate,Quantity,Dollars,Freight,Approval
105,ALTAMAR BRANDS LLC,2024-01-04,8124,2023-12-16,2024-01-20,10,214.26,3.47,Approved
4466,AMERICAN VINTAGE BEVERAGE,2024-01-05,8130,2023-12-18,2024-01-22,25,370.40,8.57,Approved
388,ATLANTIC IMPORTING COMPANY,2024-01-08,8145,2023-12-20,2024-01-25,18,106.60,4.20,Approved`;

    const blob = new Blob([sampleCSV], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'sample_vendor_data_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Data Upload & Validation Pipeline</h1>
        <p className="text-xs text-slate-500 mt-1">
          Two-step ingestion workflow: Pre-validation inspection followed by Python data cleaning into MySQL.
        </p>
      </div>

      {/* Upload Zone (Matching Wireframe A) */}
      <div className="bg-white rounded-2xl border-2 border-dashed border-slate-300 p-8 text-center hover:border-indigo-500 transition">
        <div className="max-w-md mx-auto space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 mx-auto flex items-center justify-center border border-indigo-100 shadow-xs">
            <UploadCloud className="w-7 h-7" />
          </div>

          <div>
            <h3 className="text-base font-semibold text-slate-800">Upload Vendor Data File</h3>
            <p className="text-xs text-slate-500 mt-1">
              Select an Excel (.xlsx, .xls) or CSV (.csv) file to validate against dataset schema.
            </p>
          </div>

          <div className="flex items-center justify-center">
            <label className="cursor-pointer px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-xs transition">
              <span>Choose File</span>
              <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {selectedFile && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 flex items-center justify-between">
              <div className="flex items-center space-x-2 truncate">
                <FileSpreadsheet className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                <span className="font-semibold truncate">{selectedFile.name}</span>
                <span className="text-[11px] text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              </div>
              <button
                type="button"
                onClick={handleValidatePreview}
                disabled={uploading}
                className="ml-3 px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold disabled:opacity-50 transition"
              >
                {uploading ? 'Inspecting...' : 'Validate and Preview'}
              </button>
            </div>
          )}

          <div className="pt-2 flex items-center justify-center space-x-4 text-xs">
            <button
              type="button"
              onClick={downloadSampleTemplate}
              className="text-indigo-600 hover:underline flex items-center space-x-1 font-medium"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download sample template</span>
            </button>
            <span className="text-slate-300">&bull;</span>
            <span className="text-slate-500">Supports vendor invoices, purchases & inventory</span>
          </div>
        </div>
      </div>

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center space-x-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Validation & Preview Card */}
      {preview && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-slate-900">{preview.file_name}</h3>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  preview.validation_status === 'VALID' ? 'bg-emerald-100 text-emerald-800' :
                  preview.validation_status === 'WARNING' ? 'bg-amber-100 text-amber-800' :
                  'bg-rose-100 text-rose-800'
                }`}>
                  {preview.validation_status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Detected Schema: <span className="font-semibold text-slate-700 font-mono">{preview.detected_type}</span> &bull; {preview.total_rows.toLocaleString()} estimated rows &bull; {preview.total_columns} columns
              </p>
            </div>

            <button
              type="button"
              onClick={handleConfirmImport}
              disabled={confirming || preview.validation_status === 'INVALID'}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 shadow-xs disabled:opacity-50 transition flex items-center space-x-1.5"
            >
              {confirming ? (
                <span>Cleaning & Importing...</span>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>Confirm and Import Dataset</span>
                </>
              )}
            </button>
          </div>

          {/* Validation Messages & Cleaning Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-2">
                Validation Assessment
              </span>
              <ul className="space-y-1.5 text-xs text-slate-600">
                {(preview.validation_messages || []).map((msg, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0"></span>
                    <span>{msg}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100">
              <span className="text-xs font-semibold text-indigo-900 uppercase tracking-wider block mb-2">
                Documented Cleaning Actions (Applied Upon Import)
              </span>
              <ul className="space-y-1.5 text-xs text-indigo-950">
                {(preview.cleaning_actions_summary || []).map((act, i) => (
                  <li key={i} className="flex items-start space-x-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <span>{act}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Preview Rows Table */}
          <div>
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Sample Data Rows (First 10 records)
            </h4>
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="min-w-full text-left text-xs divide-y divide-slate-200">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold">
                  <tr>
                    {(preview.columns || []).map((col) => (
                      <th key={col} className="py-2.5 px-3 whitespace-nowrap">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {(preview.preview_rows || []).map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50">
                      {(preview.columns || []).map((col) => (
                        <td key={col} className="py-2 px-3 whitespace-nowrap font-mono text-[11px]">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'NULL'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Ingestion Batch Audit History */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-base font-semibold text-slate-800 mb-1">Batch Ingestion Audit History</h3>
        <p className="text-xs text-slate-500 mb-4">Historical file uploads tracked in upload_batches MySQL table</p>

        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-xs divide-y divide-slate-100">
            <thead>
              <tr className="text-slate-400 font-semibold uppercase">
                <th className="py-2.5 px-3">Batch ID</th>
                <th className="py-2.5 px-3">File Name</th>
                <th className="py-2.5 px-3">Detected Type</th>
                <th className="py-2.5 px-3 text-right">Row Count</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-right">Uploaded At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 text-slate-700">
              {uploadHistory.map((batch) => (
                <tr key={batch.upload_id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-mono text-slate-500">#{batch.upload_id}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-900">{batch.file_name}</td>
                  <td className="py-2.5 px-3 text-slate-600 font-mono">{batch.file_type}</td>
                  <td className="py-2.5 px-3 text-right font-medium">{batch.row_count?.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {batch.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-500">{batch.uploaded_at?.split('T')[0]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DataUpload;
