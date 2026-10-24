import React, { useState, useEffect } from 'react';
import { Filter, RotateCcw, Search } from 'lucide-react';
import { vendorAPI } from '../services/api';

const FilterBar = ({ onFilterChange, showCategory = true, showSearch = true }) => {
  const [vendors, setVendors] = useState([]);
  const [selectedVendor, setSelectedVendor] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    vendorAPI.getVendors({ page_size: 100 })
      .then((res) => {
        if (res.data && res.data.vendors) {
          setVendors(res.data.vendors);
        }
      })
      .catch((err) => console.error('Error fetching vendors for filter', err));
  }, []);

  const handleApply = (e) => {
    if (e) e.preventDefault();
    onFilterChange({
      vendor_id: selectedVendor ? Number(selectedVendor) : undefined,
      category: selectedCategory !== 'All' ? selectedCategory : undefined,
      search: searchTerm.trim() || undefined,
    });
  };

  const handleReset = () => {
    setSelectedVendor('');
    setSelectedCategory('All');
    setSearchTerm('');
    onFilterChange({});
  };

  return (
    <form onSubmit={handleApply} className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs mb-6">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mr-2">
          <Filter className="w-3.5 h-3.5 text-indigo-600" />
          <span>Filters:</span>
        </div>

        {showSearch && (
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search vendor name or number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition"
            />
          </div>
        )}

        <div className="min-w-[180px]">
          <select
            value={selectedVendor}
            onChange={(e) => setSelectedVendor(e.target.value)}
            className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white"
          >
            <option value="">All Vendors</option>
            {vendors.map((v) => (
              <option key={v.vendor_id} value={v.vendor_id}>
                {v.vendor_name} ({v.vendor_number})
              </option>
            ))}
          </select>
        </div>

        {showCategory && (
          <div className="min-w-[160px]">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 bg-white"
            >
              <option value="All">All Categories</option>
              <option value="Beverage & Spirits">Beverage & Spirits</option>
              <option value="Spirits & Hard Liquor">Spirits & Hard Liquor</option>
              <option value="Wine & Champagne">Wine & Champagne</option>
              <option value="Craft Beer & Malt">Craft Beer & Malt</option>
            </select>
          </div>
        )}

        <div className="flex items-center space-x-2 ml-auto">
          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white shadow-xs transition"
          >
            Apply Filters
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="p-1.5 text-xs font-medium rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-600 transition"
            title="Reset Filters"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </form>
  );
};

export default FilterBar;
