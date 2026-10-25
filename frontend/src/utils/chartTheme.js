export const getChartConfig = (isDark) => {
  return {
    grid: {
      stroke: isDark ? '#293548' : '#e2e8f0',
      strokeDasharray: '3 3',
    },
    axis: {
      stroke: isDark ? '#94a3b8' : '#64748b',
      tick: {
        fill: isDark ? '#94a3b8' : '#64748b',
        fontSize: 11,
      },
      tickSmall: {
        fill: isDark ? '#94a3b8' : '#64748b',
        fontSize: 10,
      },
    },
    tooltip: {
      contentStyle: {
        backgroundColor: isDark ? '#172033' : '#1e293b',
        borderColor: isDark ? '#293548' : '#334155',
        borderRadius: '8px',
        color: '#f1f5f9',
        fontSize: '12px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
      },
      itemStyle: {
        color: '#f1f5f9',
      },
    },
    legend: {
      wrapperStyle: {
        fontSize: '11px',
        color: isDark ? '#94a3b8' : '#64748b',
      },
    },
    colors: {
      primary: isDark ? '#60a5fa' : '#6366f1',
      secondary: isDark ? '#34d399' : '#10b981',
      accent: isDark ? '#fbbf24' : '#f59e0b',
      purple: isDark ? '#a78bfa' : '#8b5cf6',
      pink: isDark ? '#f472b6' : '#ec4899',
      sky: isDark ? '#38bdf8' : '#0284c7',
      radar: isDark
        ? ['#60a5fa', '#34d399', '#fbbf24', '#f472b6', '#a78bfa']
        : ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#3b82f6'],
      pie: isDark
        ? ['#60a5fa', '#34d399', '#fbbf24', '#f472b6', '#a78bfa', '#38bdf8']
        : ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'],
    },
  };
};
