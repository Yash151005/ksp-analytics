import React, { useState, useEffect } from 'react';
import { reportsAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage, OllamaInsightBox } from '../components/Shared';
import dayjs from 'dayjs';

export const Reports = () => {
  const [reports, setReports] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showGenerator, setShowGenerator] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedReport, setGeneratedReport] = useState(null);
  const [narrativeText, setNarrativeText] = useState('');
  const [isGeneratingNarrative, setIsGeneratingNarrative] = useState(false);
  const [editingReportId, setEditingReportId] = useState(null);

  const [formData, setFormData] = useState({
    title: '',
    template: '',
    dateFrom: dayjs().subtract(30, 'days').format('YYYY-MM-DD'),
    dateTo: dayjs().format('YYYY-MM-DD'),
    districts: '',
    crimeTypes: '',
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [reportsRes, templatesRes] = await Promise.all([
          reportsAPI.list({ limit: 20 }),
          reportsAPI.getTemplates(),
        ]);
        setReports(reportsRes.data.data);
        setTemplates(templatesRes.data.templates);
        setError(null);
      } catch (err) {
        setError('Failed to load reports');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      if (editingReportId) {
        await reportsAPI.update(editingReportId, {
          title: formData.title,
          report_type: formData.template,
          districts: formData.districts,
          crime_types: formData.crimeTypes,
        });
        const reportsRes = await reportsAPI.list({ limit: 20 });
        setReports(reportsRes.data.data);
        setShowGenerator(false);
        setEditingReportId(null);
      } else {
        const response = await reportsAPI.generate({
          title: formData.title,
          report_type: formData.template,
          date_from: `${formData.dateFrom}T00:00:00`,
          date_to: `${formData.dateTo}T23:59:59`,
          districts: formData.districts,
          crime_types: formData.crimeTypes,
        });
        setGeneratedReport(response.data);
        const reportsRes = await reportsAPI.list({ limit: 20 });
        setReports(reportsRes.data.data);
      }
      setError(null);
    } catch (err) {
      setError(editingReportId ? 'Failed to update report' : 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleEditReport = async (report, e) => {
    e.stopPropagation();
    try {
      const response = await reportsAPI.get(report.id);
      const fullReport = response.data;
      setFormData({
        title: fullReport.title || '',
        template: fullReport.report_type || '',
        dateFrom: fullReport.date_from ? dayjs(fullReport.date_from).format('YYYY-MM-DD') : '',
        dateTo: fullReport.date_to ? dayjs(fullReport.date_to).format('YYYY-MM-DD') : '',
        districts: fullReport.districts ? fullReport.districts.join(', ') : '',
        crimeTypes: fullReport.crime_types ? fullReport.crime_types.join(', ') : '',
      });
      setEditingReportId(report.id);
      setShowGenerator(true);
      setGeneratedReport(null);
    } catch (err) {
      setError('Failed to load report for editing');
    }
  };

  const handleDeleteReport = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await reportsAPI.delete(id);
      setReports(reports.filter((r) => r.id !== id));
      if (generatedReport && generatedReport.id === id) {
        setGeneratedReport(null);
      }
    } catch (err) {
      setError('Failed to delete report');
    }
  };

  const handleViewReport = async (reportId) => {
    try {
      const response = await reportsAPI.get(reportId);
      setGeneratedReport(response.data);
      if (response.data.narrative_summary) {
        setNarrativeText(response.data.narrative_summary);
      } else {
        setNarrativeText('');
      }
      setShowGenerator(false);
      window.scrollTo(0, 0);
    } catch (err) {
      setError('Failed to load report details');
    }
  };

  const generateNarrative = async () => {
    if (!generatedReport) return;
    
    setIsGeneratingNarrative(true);
    setNarrativeText('');
    try {
      const response = await reportsAPI.export(generatedReport.id, 'json');
      const reader = response.data.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

        for (const line of lines) {
          const jsonStr = line.replace('data: ', '').trim();
          if (jsonStr && jsonStr !== '[DONE]') {
            try {
              const data = JSON.parse(jsonStr);
              setNarrativeText(prev => prev + (data.content || ''));
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      setNarrativeText('Error generating narrative.');
    } finally {
      setIsGeneratingNarrative(false);
    }
  };

  const handleExport = async (format) => {
    if (!generatedReport) return;
    try {
      const response = await reportsAPI.export(generatedReport.id, format);
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `${generatedReport.title.replace(/ /g, '_')}_${dayjs().format('YYYYMMDD')}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match && match.length > 1) {
          filename = match[1];
        }
      }
      
      // Download file
      const link = document.createElement('a');
      link.href = URL.createObjectURL(new Blob([response.data]));
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading && reports.length === 0) return <LoadingSpinner text="Loading reports..." />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Reports & Export</h1>
        <p className="text-gray-400">Generate custom crime analytics reports</p>
      </div>

      {/* Report Generator */}
      {!showGenerator ? (
        <button
          onClick={() => setShowGenerator(true)}
          className="bg-amber text-navy hover:bg-opacity-90 transition font-bold py-3 px-6 rounded-lg self-start"
        >
          📝 Create New Report
        </button>
      ) : (
        <div className="bg-steel-blue rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">New Report</h2>
          
          <div className="space-y-4">
            <div>
              <label className="text-gray-300 text-sm block mb-2">Report Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Weekly District Report"
                className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
              />
            </div>

            <div>
              <label className="text-gray-300 text-sm block mb-2">Template (Optional)</label>
              <select
                value={formData.template}
                onChange={(e) => setFormData({ ...formData, template: e.target.value })}
                className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
              >
                <option value="">Custom Report</option>
                {templates.map((template) => (
                  <option key={template} value={template}>
                    {template}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-gray-300 text-sm block mb-2">From Date</label>
                <input
                  type="date"
                  value={formData.dateFrom}
                  onChange={(e) => setFormData({ ...formData, dateFrom: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
              </div>
              <div>
                <label className="text-gray-300 text-sm block mb-2">To Date</label>
                <input
                  type="date"
                  value={formData.dateTo}
                  onChange={(e) => setFormData({ ...formData, dateTo: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
              </div>
            </div>

            <div>
              <label className="text-gray-300 text-sm block mb-2">Districts (comma-separated)</label>
              <input
                type="text"
                value={formData.districts}
                onChange={(e) => setFormData({ ...formData, districts: e.target.value })}
                placeholder="e.g., Bengaluru Urban, Mysuru"
                className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
              />
            </div>

            <div>
              <label className="text-gray-300 text-sm block mb-2">Crime Types (comma-separated)</label>
              <input
                type="text"
                value={formData.crimeTypes}
                onChange={(e) => setFormData({ ...formData, crimeTypes: e.target.value })}
                placeholder="e.g., theft, assault, fraud"
                className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
              />
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleGenerateReport}
                disabled={generating}
                className="flex-1 bg-amber text-navy hover:bg-opacity-90 transition disabled:opacity-50 font-bold py-2 px-4 rounded-lg"
              >
                {generating ? (editingReportId ? 'Updating...' : 'Generating...') : (editingReportId ? '✓ Update Report' : '✓ Generate Report')}
              </button>
              <button
                onClick={() => {
                  setShowGenerator(false);
                  setEditingReportId(null);
                  setGeneratedReport(null);
                  setFormData({
                    title: '',
                    template: '',
                    dateFrom: dayjs().subtract(30, 'days').format('YYYY-MM-DD'),
                    dateTo: dayjs().format('YYYY-MM-DD'),
                    districts: '',
                    crimeTypes: '',
                  });
                }}
                className="flex-1 bg-gray-600 hover:bg-gray-700 transition font-bold py-2 px-4 rounded-lg text-white"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generated Report */}
      {generatedReport && (
        <div className="bg-steel-blue rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-4">{generatedReport.title}</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-navy p-3 rounded">
              <p className="text-gray-400 text-xs">Total Crimes</p>
              <p className="text-2xl font-bold text-amber">{generatedReport.metrics.total_crimes}</p>
            </div>
            <div className="bg-navy p-3 rounded">
              <p className="text-gray-400 text-xs">Clearance Rate</p>
              <p className="text-2xl font-bold text-safe-green">{(generatedReport.metrics.avg_clearance_rate || 0).toFixed(1)}%</p>
            </div>
            <div className="bg-navy p-3 rounded">
              <p className="text-gray-400 text-xs">Avg Severity</p>
              <p className="text-2xl font-bold text-alert-red">{(generatedReport.metrics.avg_severity || 0).toFixed(1)}</p>
            </div>
            <div className="bg-navy p-3 rounded">
              <p className="text-gray-400 text-xs">Districts Covered</p>
              <p className="text-2xl font-bold text-blue-400">{generatedReport.districts?.length || 0}</p>
            </div>
          </div>

          <div className="bg-navy p-4 rounded mb-6 text-sm">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-gray-400 font-bold block mb-1">Districts</span>
                <span className="text-white">{(generatedReport.districts && generatedReport.districts.length > 0) ? generatedReport.districts.join(', ') : 'All Districts'}</span>
              </div>
              <div>
                <span className="text-gray-400 font-bold block mb-1">Crime Types</span>
                <span className="text-white">{(generatedReport.crime_types && generatedReport.crime_types.length > 0) ? generatedReport.crime_types.join(', ') : 'All Types'}</span>
              </div>
              <div>
                <span className="text-gray-400 font-bold block mb-1">From Date</span>
                <span className="text-white">{dayjs(generatedReport.date_from).format('DD-MM-YYYY')}</span>
              </div>
              <div>
                <span className="text-gray-400 font-bold block mb-1">To Date</span>
                <span className="text-white">{dayjs(generatedReport.date_to).format('DD-MM-YYYY')}</span>
              </div>
            </div>
          </div>

          {/* AI Narrative */}
          <OllamaInsightBox
            title="AI-Generated Summary"
            icon="📝"
            content={narrativeText}
            isStreaming={isGeneratingNarrative}
            onGenerate={generateNarrative}
          />

          {/* Export Options */}
          <div className="mt-6 flex gap-3 flex-wrap">
            <button
              onClick={() => handleExport('pdf')}
              className="bg-alert-red hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
            >
              📄 Export PDF
            </button>
            <button
              onClick={() => handleExport('csv')}
              className="bg-safe-green hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
            >
              📊 Export CSV
            </button>
            <button
              onClick={() => handleExport('json')}
              className="bg-blue-500 hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
            >
              {'{}'} Export JSON
            </button>
            <button
              onClick={() => handleExport('xlsx')}
              className="bg-amber text-navy hover:bg-opacity-80 transition font-bold py-2 px-4 rounded"
            >
              📈 Export Excel
            </button>
          </div>
        </div>
      )}

      {/* Previous Reports */}
      {!showGenerator && (
        <div className="bg-steel-blue rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Recent Reports</h2>
          <div className="space-y-2">
            {reports.map((report) => (
              <div 
                key={report.id} 
                className="bg-navy p-4 rounded flex justify-between items-center hover:bg-opacity-80 transition cursor-pointer"
                onClick={() => {
                  handleViewReport(report.id);
                }}
              >
                <div>
                  <p className="text-white font-bold">{report.title}</p>
                  <p className="text-gray-400 text-sm">
                    {dayjs(report.date_from).format('MMM DD')} - {dayjs(report.date_to).format('MMM DD, YYYY')}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-amber text-xs font-semibold bg-amber/20 px-3 py-1 rounded">
                    {report.report_type}
                  </span>
                  <button 
                    onClick={(e) => handleEditReport(report, e)}
                    className="text-gray-400 hover:text-white transition"
                    title="Edit Report"
                  >
                    ✏️
                  </button>
                  <button 
                    onClick={(e) => handleDeleteReport(report.id, e)}
                    className="text-gray-400 hover:text-alert-red transition"
                    title="Delete Report"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
