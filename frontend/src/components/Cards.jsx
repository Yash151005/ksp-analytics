import React from 'react';

export const KPICard = ({ title, value, subtitle, change, icon, color = 'amber' }) => {
  const colorClasses = {
    amber: 'bg-amber text-navy',
    red: 'bg-alert-red text-white',
    green: 'bg-safe-green text-white',
    blue: 'bg-steel-blue text-white',
  };

  return (
    <div className="bg-steel-blue rounded-lg p-6 text-white">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-300 text-sm mb-2">{title}</p>
          <h3 className="text-3xl font-bold mb-2">{typeof value === 'number' ? value.toLocaleString() : value}</h3>
          {subtitle && <p className="text-gray-400 text-sm">{subtitle}</p>}
          {change && (
            <p className={`text-sm mt-2 ${change >= 0 ? 'text-alert-red' : 'text-safe-green'}`}>
              {change >= 0 ? '↑' : '↓'} {Math.abs(change)}% from last period
            </p>
          )}
        </div>
        {icon && <div className="text-4xl">{icon}</div>}
      </div>
    </div>
  );
};

export const RiskScoreBadge = ({ score, size = 'md' }) => {
  const getColor = () => {
    if (score >= 70) return 'bg-alert-red text-white';
    if (score >= 40) return 'bg-amber text-navy';
    return 'bg-safe-green text-white';
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-3 text-lg',
  };

  return (
    <span className={`${getColor()} rounded-full font-bold ${sizeClasses[size]} inline-flex items-center justify-center min-w-[3rem]`}>
      {Math.round(score)}%
    </span>
  );
};

export const AlertCard = ({ alert, onAction }) => {
  const severityColors = {
    critical: 'border-l-4 border-alert-red bg-red-900/20',
    high: 'border-l-4 border-amber bg-amber/20',
    medium: 'border-l-4 border-blue-500 bg-blue-900/20',
    low: 'border-l-4 border-safe-green bg-green-900/20',
  };

  const severityBadgeColors = {
    critical: 'bg-alert-red',
    high: 'bg-amber',
    medium: 'bg-blue-500',
    low: 'bg-safe-green',
  };

  return (
    <div className={`${severityColors[alert.severity] || severityColors.low} p-4 rounded-lg text-white mb-3`}>
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-bold">{alert.title}</h4>
        <span className={`${severityBadgeColors[alert.severity]} text-white text-xs px-2 py-1 rounded-full font-semibold`}>
          {alert.severity.toUpperCase()}
        </span>
      </div>
      <p className="text-gray-300 text-sm mb-2">{alert.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>📍 {alert.affected_area}</span>
        <span>{new Date(alert.created_at).toLocaleDateString()}</span>
      </div>
      {alert.ollama_recommendation && (
        <div className="mt-3 p-2 bg-black/30 rounded text-sm text-gray-200">
          <strong>AI Recommendation:</strong> {alert.ollama_recommendation.substring(0, 100)}...
        </div>
      )}
      {onAction && (
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => onAction('acknowledge', alert.id)}
            className="flex-1 bg-steel-blue hover:bg-opacity-80 transition px-3 py-2 rounded text-xs font-semibold"
          >
            Acknowledge
          </button>
          <button
            onClick={() => onAction('escalate', alert.id)}
            className="flex-1 bg-alert-red hover:bg-opacity-80 transition px-3 py-2 rounded text-xs font-semibold"
          >
            Escalate
          </button>
        </div>
      )}
    </div>
  );
};

export const CrimeTable = ({ crimes, onRowClick, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="bg-steel-blue rounded-lg p-8 text-center text-gray-400">
        Loading crime data...
      </div>
    );
  }

  if (!crimes || crimes.length === 0) {
    return (
      <div className="bg-steel-blue rounded-lg p-8 text-center text-gray-400">
        No crimes found
      </div>
    );
  }

  return (
    <div className="bg-steel-blue rounded-lg overflow-x-auto">
      <table className="w-full text-sm text-gray-300">
        <thead className="bg-navy border-b border-gray-600">
          <tr>
            <th className="px-4 py-3 text-left font-semibold">Crime ID</th>
            <th className="px-4 py-3 text-left font-semibold">Type</th>
            <th className="px-4 py-3 text-left font-semibold">District</th>
            <th className="px-4 py-3 text-left font-semibold">Date</th>
            <th className="px-4 py-3 text-left font-semibold">Status</th>
            <th className="px-4 py-3 text-left font-semibold">Severity</th>
          </tr>
        </thead>
        <tbody>
          {crimes.map((crime) => (
            <tr
              key={crime.id}
              onClick={() => onRowClick?.(crime)}
              className="border-b border-gray-700 hover:bg-navy transition cursor-pointer"
            >
              <td className="px-4 py-3 font-mono text-amber">{crime.crime_id}</td>
              <td className="px-4 py-3">{crime.type}</td>
              <td className="px-4 py-3">{crime.district}</td>
              <td className="px-4 py-3">{new Date(crime.date).toLocaleDateString()}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  crime.status === 'closed' ? 'bg-safe-green text-white' :
                  crime.status === 'under_investigation' ? 'bg-amber text-navy' :
                  'bg-gray-600 text-white'
                }`}>
                  {crime.status}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`font-bold ${
                  crime.severity >= 4 ? 'text-alert-red' :
                  crime.severity >= 3 ? 'text-amber' :
                  'text-safe-green'
                }`}>
                  {crime.severity}/5
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default { KPICard, RiskScoreBadge, AlertCard, CrimeTable };
