import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  ShoppingCart, 
  Package, 
  GitCompare, 
  UploadCloud, 
  FileSpreadsheet,
  Award
} from 'lucide-react';

const navItems = [
  { name: 'User Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Vendor Analytics', path: '/vendors', icon: Users },
  { name: 'Purchase & Sales', path: '/purchases-sales', icon: ShoppingCart },
  { name: 'Inventory Analytics', path: '/inventory', icon: Package },
  { name: 'Vendor Comparison', path: '/comparison', icon: GitCompare },
  { name: 'Data Upload', path: '/upload', icon: UploadCloud },
  { name: 'Reports & Export', path: '/reports', icon: FileSpreadsheet },
];

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 hidden md:flex flex-col flex-shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4">
        <p className="px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Navigation Modules
        </p>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 shadow-sm border border-indigo-100/60 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4 border-t border-slate-200">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs">
          <div className="flex items-center space-x-2 text-slate-700 font-semibold mb-1">
            <Award className="w-4 h-4 text-amber-500" />
            <span>CVPI Scoring Engine</span>
          </div>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Standardized composite index ranking across delivery SLA, commercial margins, and stock velocity.
          </p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
