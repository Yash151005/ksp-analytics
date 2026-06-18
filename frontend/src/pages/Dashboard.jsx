import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { KPICard, CrimeTable, AlertCard } from '../components/Cards';
import { OllamaInsightBox, LoadingSpinner, ErrorMessage } from '../components/Shared';
import { crimesAPI, alertsAPI, aiAPI } from '../services/api';
import dayjs from 'dayjs';

export const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [typeDistribution, setTypeDistribution] = useState([]);
  const [districtStats, setDistrictStats] = useState([]);
  const [recentCrimes, setRecentCrimes] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [briefingText, setBriefingText] = useState('');
  const [isGeneratingBriefing, setIsGeneratingBriefing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const COLORS = ['#F59E0B', '#1E3A5F', '#DC2626', '#16A34A', '#6B7280'];

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [summaryRes, trendRes, typeRes, districtRes, crimesRes, alertsRes] = await Promise.all([
          crimesAPI.getSummary(30),
          crimesAPI.getTrend(12),
          crimesAPI.getByType(30),
          crimesAPI.getByDistrict(30),
          crimesAPI.list({ limit: 10 }),
          alertsAPI.list({ limit: 5, days: 30 }),
        ]);

        setSummary(summaryRes.data);
        setTrend(trendRes.data);
        
        // Transform type distribution
        const typeData = Object.entries(typeRes.data).map(([type, count]) => ({
          name: type.charAt(0).toUpperCase() + type.slice(1),
          value: count,
        }));
        setTypeDistribution(typeData);

        // Transform district stats
        const districtData = Object.entries(districtRes.data)
          .map(([district, count]) => ({
            name: district.length > 15 ? district.substring(0, 12) + '...' : district,
            fullName: district,
            count,
          }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);
        setDistrictStats(districtData);

        setRecentCrimes(crimesRes.data.data);
        setAlerts(alertsRes.data.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load dashboard');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const generateBriefing = async () => {
    setIsGeneratingBriefing(true);
    setBriefingText('');
    console.log('Generating AI briefing...');
    try {
      await aiAPI.getBriefing(
        (chunk) => {
          if (chunk) {
            setBriefingText((prev) => prev + chunk);
          }
        },
        (err) => {
          console.error(err);
          setBriefingText(err?.message || 'Error generating briefing. Check if Ollama is running.');
        }
      );
    } catch (err) {
      setBriefingText(err?.message || 'Error generating briefing. Check if Ollama is running.');
      console.error(err);
    } finally {
      setIsGeneratingBriefing(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading dashboard data..." />;
  if (error) return <ErrorMessage title="Dashboard Error" message={error} />;

  const stats = summary || {};

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-bold text-white">Executive Dashboard</h1>
        <p className="text-gray-400">Real-time crime analytics for Karnataka State Police</p>
      </div>

      {/* Live Alert */}
      {alerts.length > 0 && (
        <div className="bg-alert-red/20 border border-alert-red rounded-lg p-4 text-white flex items-start gap-4">
          <span className="text-2xl animate-pulse">🚨</span>
          <div className="flex-1">
            <strong>Live Alert:</strong> {alerts[0].title} - {alerts[0].affected_area}
            <br />
            <span className="text-sm text-gray-300">{new Date(alerts[0].created_at).toLocaleString()}</span>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard
          title="Total Crimes (30d)"
          value={stats.total_crimes || 0}
          icon="📊"
          color="amber"
        />
        <KPICard
          title="Clearance Rate"
          value={`${stats.clearance_rate?.toFixed(1)}%` || '0%'}
          icon="✅"
          color="green"
        />
        <KPICard
          title="Active Cases"
          value={stats.open_crimes || 0}
          icon="📋"
          color="blue"
        />
        <KPICard
          title="Under Investigation"
          value={stats.under_investigation || 0}
          icon="🔍"
          color="amber"
        />
        <KPICard
          title="High-Risk Zones"
          value={districtStats.length || 0}
          icon="⚠️"
          color="red"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Crime Trend */}
        <div className="bg-steel-blue rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Crime Trend (Last 12 Months)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="date" stroke="#999" />
              <YAxis stroke="#999" />
              <Tooltip contentStyle={{ backgroundColor: '#0A1628', border: '1px solid #F59E0B' }} />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#F59E0B"
                dot={{ fill: '#F59E0B' }}
                strokeWidth={2}
                name="Crimes"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Crime Type Distribution */}
        <div className="bg-steel-blue rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Crime Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={typeDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {typeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#0A1628', border: '1px solid #F59E0B' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* District Wise Comparison */}
        <div className="bg-steel-blue rounded-lg p-6 lg:col-span-2">
          <h3 className="text-lg font-bold text-white mb-4">Top 10 Districts by Crime Count</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={districtStats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="name" stroke="#999" />
              <YAxis stroke="#999" />
              <Tooltip
                contentStyle={{ backgroundColor: '#0A1628', border: '1px solid #F59E0B' }}
                formatter={(value) => [value, 'Crimes']}
              />
              <Bar dataKey="count" fill="#F59E0B" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Insight */}
      <OllamaInsightBox
        title="Daily AI Briefing"
        icon="🤖"
        content={briefingText}
        isStreaming={isGeneratingBriefing}
        onGenerate={generateBriefing}
      />

      {/* Recent Crimes Table */}
      <div className="bg-steel-blue rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Recent Crimes</h3>
        <CrimeTable crimes={recentCrimes} />
      </div>

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <div className="bg-steel-blue rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert) => (
              <AlertCard key={alert.id} alert={alert} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
