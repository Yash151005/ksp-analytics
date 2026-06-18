import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Shared';
import { AlertCard } from '../components/Cards';

export const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [filters, setFilters] = useState({
    severity: '',
    acknowledged: '',
    days: 30,
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const params = { ...filters };
        if (filters.acknowledged !== '') {
          params.acknowledged = filters.acknowledged === 'true';
        } else {
          delete params.acknowledged;
        }
        const response = await alertsAPI.list(params);
        setAlerts(response.data.data);
        setTotal(response.data.total);
        setError(null);
      } catch (err) {
        setError('Failed to load alerts');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [filters, refreshKey]);

  const handleAction = async (action, alertId) => {
    try {
      if (action === 'acknowledge') {
        await alertsAPI.acknowledge(alertId);
        // Update alert in local state
        setAlerts((prev) => prev.map((a) =>
          a.id === alertId ? { ...a, is_acknowledged: true } : a
        ));
      } else if (action === 'escalate') {
        const response = await alertsAPI.escalate(alertId);
        // Update alert in local state with new severity
        setAlerts((prev) => prev.map((a) =>
          a.id === alertId ? { ...a, severity: response.data.new_severity } : a
        ));
      }
      setRefreshKey((key) => key + 1);
    } catch (err) {
      console.error(err);
    }
  };

  const severityCounts = {
    critical: alerts.filter(a => a.severity === 'critical').length,
    high: alerts.filter(a => a.severity === 'high').length,
    medium: alerts.filter(a => a.severity === 'medium').length,
    low: alerts.filter(a => a.severity === 'low').length,
  };

  if (loading && alerts.length === 0) return <LoadingSpinner text="Loading alerts..." />;
  if (error) return <ErrorMessage title="Alerts Error" message={error} />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Crime Alerts & Anomalies</h1>
        <p className="text-gray-400">Real-time notifications of unusual crime activity</p>
      </div>

      {/* Alert Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-alert-red/20 border border-alert-red rounded-lg p-4 text-white">
          <p className="text-gray-300 text-sm">Critical</p>
          <p className="text-3xl font-bold">{severityCounts.critical}</p>
        </div>
        <div className="bg-amber/20 border border-amber rounded-lg p-4 text-white">
          <p className="text-gray-300 text-sm">High</p>
          <p className="text-3xl font-bold">{severityCounts.high}</p>
        </div>
        <div className="bg-blue-500/20 border border-blue-500 rounded-lg p-4 text-white">
          <p className="text-gray-300 text-sm">Medium</p>
          <p className="text-3xl font-bold">{severityCounts.medium}</p>
        </div>
        <div className="bg-safe-green/20 border border-safe-green rounded-lg p-4 text-white">
          <p className="text-gray-300 text-sm">Low</p>
          <p className="text-3xl font-bold">{severityCounts.low}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-steel-blue rounded-lg p-4 grid grid-cols-1 md:grid-cols-4 gap-4">
        <select
          value={filters.severity}
          onChange={(e) => setFilters({ ...filters, severity: e.target.value, offset: 0 })}
          className="bg-navy text-white px-3 py-2 rounded border border-gray-600"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={filters.acknowledged}
          onChange={(e) => setFilters({ ...filters, acknowledged: e.target.value, offset: 0 })}
          className="bg-navy text-white px-3 py-2 rounded border border-gray-600"
        >
          <option value="">All</option>
          <option value="false">Unacknowledged</option>
          <option value="true">Acknowledged</option>
        </select>

        <select
          value={filters.days}
          onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value), offset: 0 })}
          className="bg-navy text-white px-3 py-2 rounded border border-gray-600"
        >
          <option value="1">Last 24 Hours</option>
          <option value="7">Last 7 Days</option>
          <option value="30">Last 30 Days</option>
          <option value="90">Last 90 Days</option>
        </select>

        <button
          onClick={() => setFilters({ ...filters, offset: 0 })}
          className="bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded"
        >
          🔍 Filter
        </button>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onAction={handleAction}
          />
        ))}
      </div>

      {alerts.length === 0 && (
        <div className="bg-steel-blue rounded-lg p-8 text-center text-gray-400">
          No alerts found for selected filters
        </div>
      )}

      {/* Pagination */}
      {total > filters.limit && (
        <div className="flex justify-center gap-4">
          <button
            onClick={() => setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) })}
            disabled={filters.offset === 0}
            className="disabled:opacity-50 bg-amber text-navy font-bold py-2 px-4 rounded"
          >
            ← Previous
          </button>
          <span className="text-white flex items-center">
            Page {Math.floor(filters.offset / filters.limit) + 1}
          </span>
          <button
            onClick={() => setFilters({ ...filters, offset: filters.offset + filters.limit })}
            disabled={filters.offset + filters.limit >= total}
            className="disabled:opacity-50 bg-amber text-navy font-bold py-2 px-4 rounded"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default Alerts;
