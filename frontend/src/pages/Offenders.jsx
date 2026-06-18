import React, { useState, useEffect } from 'react';
import { criminalsAPI, aiAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage, OllamaInsightBox, ConfirmDialog } from '../components/Shared';
import { RiskScoreBadge } from '../components/Cards';

export const Offenders = () => {
  const [criminals, setCriminals] = useState([]);
  const [total, setTotal] = useState(0);
  const [selectedCriminal, setSelectedCriminal] = useState(null);
  const [profileText, setProfileText] = useState('');
  const [isGeneratingProfile, setIsGeneratingProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  
  const [filters, setFilters] = useState({
    status: '',
    min_risk_score: 0,
    max_risk_score: 100,
    search: '',
    limit: 50,
    offset: 0,
  });

  useEffect(() => {
    const fetchCriminals = async () => {
      try {
        setLoading(true);
        const response = await criminalsAPI.list(filters);
        setCriminals(response.data.data);
        setTotal(response.data.total);
        setError(null);
      } catch (err) {
        setError('Failed to load criminals');
      } finally {
        setLoading(false);
      }
    };

    fetchCriminals();
  }, [filters]);

  const generateProfile = async (criminal) => {
    setIsGeneratingProfile(true);
    setProfileText('');
    try {
      await aiAPI.generateProfile(
        criminal.id,
        (chunk) => {
          if (chunk) {
            setProfileText((prev) => prev + chunk);
          }
        },
        (err) => {
          console.error(err);
          setProfileText('Error generating profile.');
        }
      );
    } catch (err) {
      setProfileText('Error generating profile.');
    } finally {
      setIsGeneratingProfile(false);
    }
  };

  const handleRowClick = (criminal) => {
    setSelectedCriminal(criminal);
    setShowProfile(true);
  };

  if (loading && criminals.length === 0) return <LoadingSpinner text="Loading offender records..." />;
  if (error) return <ErrorMessage title="Data Error" message={error} />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Repeat Offender Tracker</h1>
        <p className="text-gray-400">Monitor high-risk criminals and known repeat offenders</p>
      </div>

      {/* Filters */}
      <div className="bg-steel-blue rounded-lg p-4 grid grid-cols-1 md:grid-cols-5 gap-4">
        <input
          type="text"
          placeholder="Search by name, alias, or ID..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value, offset: 0 })}
          className="col-span-1 md:col-span-2 bg-navy text-white px-3 py-2 rounded border border-gray-600"
        />

        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value, offset: 0 })}
          className="bg-navy text-white px-3 py-2 rounded border border-gray-600"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="arrested">Arrested</option>
          <option value="absconding">Absconding</option>
        </select>

        <input
          type="range"
          min="0"
          max="100"
          value={filters.min_risk_score}
          onChange={(e) => setFilters({ ...filters, min_risk_score: parseInt(e.target.value), offset: 0 })}
          className="col-span-1"
        />

        <button
          onClick={() => setFilters({ ...filters, offset: 0 })}
          className="bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded"
        >
          🔍 Apply
        </button>
      </div>

      {/* Table */}
      <div className="bg-steel-blue rounded-lg overflow-x-auto">
        <table className="w-full text-sm text-gray-300">
          <thead className="bg-navy border-b border-gray-600">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Name</th>
              <th className="px-4 py-3 text-left font-semibold">Alias</th>
              <th className="px-4 py-3 text-left font-semibold">Risk Score</th>
              <th className="px-4 py-3 text-left font-semibold">Active Cases</th>
              <th className="px-4 py-3 text-left font-semibold">Last Seen</th>
              <th className="px-4 py-3 text-left font-semibold">Status</th>
              <th className="px-4 py-3 text-left font-semibold">Action</th>
            </tr>
          </thead>
          <tbody>
            {criminals.map((criminal) => (
              <tr
                key={criminal.id}
                className="border-b border-gray-700 hover:bg-navy transition cursor-pointer"
              >
                <td className="px-4 py-3 font-semibold">{criminal.name}</td>
                <td className="px-4 py-3 font-mono text-amber">{criminal.alias}</td>
                <td className="px-4 py-3">
                  <RiskScoreBadge score={criminal.risk_score} size="sm" />
                </td>
                <td className="px-4 py-3">{criminal.crime_count}</td>
                <td className="px-4 py-3">{criminal.last_known_location}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                    criminal.status === 'active' ? 'bg-alert-red text-white' :
                    criminal.status === 'arrested' ? 'bg-safe-green text-white' :
                    'bg-amber text-navy'
                  }`}>
                    {criminal.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => handleRowClick(criminal)}
                    className="bg-steel-blue hover:bg-opacity-80 transition text-white px-3 py-1 rounded text-xs font-semibold"
                  >
                    View Profile
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-center gap-4">
        <button
          onClick={() => setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) })}
          disabled={filters.offset === 0}
          className="disabled:opacity-50 bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded"
        >
          ← Previous
        </button>
        <span className="text-white flex items-center">
          Page {Math.floor(filters.offset / filters.limit) + 1} of {Math.ceil(total / filters.limit)}
        </span>
        <button
          onClick={() => setFilters({ ...filters, offset: filters.offset + filters.limit })}
          disabled={filters.offset + filters.limit >= total}
          className="disabled:opacity-50 bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded"
        >
          Next →
        </button>
      </div>

      {/* Profile Modal */}
      {showProfile && selectedCriminal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-steel-blue rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="bg-navy p-4 flex justify-between items-center border-b border-gray-600">
              <h2 className="text-xl font-bold text-white">{selectedCriminal.name}</h2>
              <button
                onClick={() => setShowProfile(false)}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-400 text-sm">Alias</p>
                  <p className="font-mono text-amber">{selectedCriminal.alias}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Risk Score</p>
                  <RiskScoreBadge score={selectedCriminal.risk_score} size="md" />
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Status</p>
                  <p className="font-semibold text-white capitalize">{selectedCriminal.status}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Crime Count</p>
                  <p className="font-bold text-amber text-lg">{selectedCriminal.crime_count}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Associates</p>
                  <p className="font-bold text-safe-green">{selectedCriminal.associates_count}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Last Seen</p>
                  <p className="font-semibold">{selectedCriminal.last_known_location}</p>
                </div>
              </div>

              {/* AI Profile */}
              <div className="mt-6">
                <OllamaInsightBox
                  title="Behavioral Profile"
                  icon="🧠"
                  content={profileText}
                  isStreaming={isGeneratingProfile}
                  onGenerate={() => generateProfile(selectedCriminal)}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Offenders;
