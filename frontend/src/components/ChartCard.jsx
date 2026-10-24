import React from 'react';

const ChartCard = ({ title, subtitle, children, headerRight, className = '' }) => {
  return (
    <div className={`bg-white rounded-xl border border-slate-200 p-5 shadow-xs ${className}`}>
      <div className="flex items-start justify-between pb-4 border-b border-slate-100 mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-800">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {headerRight && <div>{headerRight}</div>}
      </div>
      <div>{children}</div>
    </div>
  );
};

export default ChartCard;
