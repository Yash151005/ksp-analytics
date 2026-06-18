import React, { useState, useEffect } from 'react';
import { analyticsAPI, aiAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage, OllamaInsightBox } from '../components/Shared';
import { RiskScoreBadge } from '../components/Cards';

export const Analytics = () => {
  const [temporalData, setTemporalData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [riskScores, setRiskScores] = useState([]);
  const [demographics, setDemographics] = useState(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [anomalyExplain, setAnomalyExplain] = useState('');
  const [isExplaining, setIsExplaining] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const [temporalRes, anomaliesRes, riskRes, demosRes] = await Promise.all([
          analyticsAPI.getTemporalHeatmap(),
          analyticsAPI.getAnomalies(2.0),
          analyticsAPI.getRiskScores(),
          analyticsAPI.getDemographics(),
        ]);

        setTemporalData(temporalRes.data.data);
        setAnomalies(anomaliesRes.data.data);
        setRiskScores(riskRes.data.data);
        setDemographics(demosRes.data.data);
        setError(null);
      } catch (err) {
        setError('Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const explainAnomaly = async (anomaly) => {
    if (!anomaly) return;
    
    setIsExplaining(true);
    setAnomalyExplain('');
    try {
      await aiAPI.explainAnomaly(
        anomaly,
        (chunk) => {
          if (chunk) {
            setAnomalyExplain((prev) => prev + chunk);
          }
        },
        (err) => {
          console.error(err);
          setAnomalyExplain(err?.message || 'Error explaining anomaly.');
        }
      );
    } catch (err) {
      setAnomalyExplain(err?.message || 'Error explaining anomaly.');
    } finally {
      setIsExplaining(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading analytics..." />;
  if (error) return <ErrorMessage title="Analytics Error" message={error} />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Crime Analytics</h1>
        <p className="text-gray-400">Temporal patterns, demographics, and predictive analysis</p>
      </div>

      {/* Section A: Temporal Analysis */}
      <div className="bg-steel-blue rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">Temporal Analysis</h2>
        <p className="text-gray-300 text-sm mb-4">Crime patterns by hour and day of week</p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-gray-300">
            <thead className="bg-navy">
              <tr>
                <th className="px-2 py-2 text-left">Hour</th>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(day => (
                  <th key={day} className="px-2 py-2 text-center">{day}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 24 }).map((_, hour) => (
                <tr key={hour} className="border-b border-gray-700">
                  <td className="px-2 py-2">{hour.toString().padStart(2, '0')}:00</td>
                  {Array.from({ length: 7 }).map((_, day) => {
                    const cell = temporalData.find(d => d.hour === hour && d.day_index === day);
                    const intensity = cell?.intensity || 0;
                    return (
                      <td
                        key={`${hour}-${day}`}
                        className="px-2 py-2 text-center"
                        style={{
                          backgroundColor: `rgba(245, 158, 11, ${intensity / 100})`,
                          color: intensity > 50 ? '#000' : '#fff',
                        }}
                      >
                        {cell?.count || 0}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section B: Demographics */}
      <div className="bg-steel-blue rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">Victim Demographics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-white font-bold mb-3">By Age</h3>
            <div className="space-y-2 text-sm">
              {demographics?.age_distribution && Object.entries(demographics.age_distribution)
                .sort()
                .map(([age, count]) => (
                  <div key={age} className="flex justify-between">
                    <span>{age}</span>
                    <span className="font-bold text-amber">{count}</span>
                  </div>
                ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">By Gender</h3>
            <div className="space-y-2 text-sm">
              {demographics?.gender_distribution && Object.entries(demographics.gender_distribution)
                .map(([gender, count]) => (
                  <div key={gender} className="flex justify-between">
                    <span>{gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : 'Other'}</span>
                    <span className="font-bold text-amber">{count}</span>
                  </div>
                ))}
            </div>
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">By Occupation</h3>
            <div className="space-y-2 text-sm max-h-48 overflow-y-auto">
              {demographics?.occupation_distribution && Object.entries(demographics.occupation_distribution)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 8)
                .map(([occupation, count]) => (
                  <div key={occupation} className="flex justify-between">
                    <span className="truncate">{occupation}</span>
                    <span className="font-bold text-amber ml-2">{count}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Section C: Anomaly Detection */}
      <div className="bg-steel-blue rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">Anomaly Detection</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="space-y-2">
              {anomalies.slice(0, 5).map((anomaly, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setSelectedAnomaly(anomaly);
                    setAnomalyExplain('');
                  }}
                  className="bg-navy p-3 rounded cursor-pointer hover:bg-opacity-80 transition border-l-4 border-alert-red"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-white font-semibold">{anomaly.date}</p>
                      <p className="text-gray-400 text-sm">
                        {anomaly.crime_count} crimes (Expected: {anomaly.expected_count})
                      </p>
                    </div>
                    <span className="bg-alert-red text-white px-2 py-1 rounded text-xs font-bold">
                      {anomaly.severity}% Deviation
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <OllamaInsightBox
            title="Anomaly Explanation"
            icon="🔔"
            content={anomalyExplain}
            isStreaming={isExplaining}
            onGenerate={() => {
              if (!selectedAnomaly) {
                setAnomalyExplain('Select an anomaly to generate insights.');
                return;
              }
              explainAnomaly(selectedAnomaly);
            }}
          />
        </div>
      </div>

      {/* Section D: District Risk Scores */}
      <div className="bg-steel-blue rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4">District Risk Assessment</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {riskScores.slice(0, 9).map((district) => (
            <div key={district.district} className="bg-navy p-4 rounded-lg">
              <h3 className="text-white font-bold text-sm mb-2">{district.district}</h3>
              <RiskScoreBadge score={district.risk_score} size="lg" />
              <div className="mt-3 text-sm text-gray-300 space-y-1">
                <p>Crimes (30d): <span className="font-bold">{district.crime_count_30d}</span></p>
                <p>Avg Severity: <span className="font-bold">{district.avg_severity}</span></p>
                <p>Trend: <span className={`font-bold ${district.trend === 'up' ? 'text-alert-red' : 'text-safe-green'}`}>
                  {district.trend === 'up' ? '📈 Up' : '📉 Stable'}
                </span></p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
