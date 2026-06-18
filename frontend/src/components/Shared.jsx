import React, { useState, useEffect } from 'react';

export const OllamaInsightBox = ({ title, icon = '🤖', isStreaming = false, content = '', onGenerate }) => {
  const [displayedContent, setDisplayedContent] = useState('');

  // Typewriter effect for streaming
  useEffect(() => {
    if (!isStreaming && content) {
      setDisplayedContent(content);
    }
  }, [content, isStreaming]);

  return (
    <div className="bg-gradient-to-br from-steel-blue to-navy rounded-lg p-6 border border-amber/30">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">{icon}</span>
        <h3 className="text-xl font-bold text-white">{title}</h3>
        {isStreaming && (
          <div className="flex gap-1 ml-auto">
            <div className="w-2 h-2 bg-amber rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-amber rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-amber rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        )}
      </div>

      <div className="bg-navy/50 rounded-lg p-4 min-h-32 text-gray-300 font-mono text-sm leading-relaxed">
        {displayedContent || (
          <span className="text-gray-500 italic">
            {isStreaming ? 'Generating AI insights...' : 'Click generate to see AI-powered insights'}
          </span>
        )}
        {isStreaming && <span className="animate-pulse">▌</span>}
      </div>

      {onGenerate && !isStreaming && (
        <button
          onClick={onGenerate}
          className="mt-4 w-full bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded-lg"
        >
          🚀 Generate AI Insights
        </button>
      )}

      {isStreaming && (
        <div className="mt-4 text-center text-amber text-sm">
          Processing with Ollama...
        </div>
      )}
    </div>
  );
};

export const ExportButton = ({ filename, data, format = 'csv' }) => {
  const handleExport = () => {
    let content, type, url;

    if (format === 'csv') {
      content = data;
      type = 'text/csv';
    } else if (format === 'json') {
      content = JSON.stringify(data, null, 2);
      type = 'application/json';
    } else if (format === 'pdf') {
      // PDF handling requires jsPDF
      content = data;
      type = 'application/pdf';
    }

    const element = document.createElement('a');
    const file = new Blob([content], { type });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <button
      onClick={handleExport}
      className="bg-steel-blue hover:bg-opacity-80 transition text-white font-semibold py-2 px-4 rounded-lg inline-flex items-center gap-2"
    >
      📥 Export {format.toUpperCase()}
    </button>
  );
};

export const LoadingSpinner = ({ text = 'Loading...' }) => (
  <div className="flex items-center justify-center p-8">
    <div className="text-center">
      <div className="inline-block">
        <div className="w-12 h-12 border-4 border-amber border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p className="text-gray-300 mt-4">{text}</p>
    </div>
  </div>
);

export const ErrorMessage = ({ title = 'Error', message, onRetry }) => (
  <div className="bg-alert-red/20 border border-alert-red rounded-lg p-6 text-white">
    <h3 className="font-bold text-lg mb-2">{title}</h3>
    <p className="text-gray-300 mb-4">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="bg-alert-red hover:bg-opacity-80 transition font-semibold py-2 px-4 rounded-lg"
      >
        Retry
      </button>
    )}
  </div>
);

export const ConfirmDialog = ({ title, message, onConfirm, onCancel, isDangerous = false }) => (
  <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
    <div className="bg-steel-blue rounded-lg p-6 max-w-sm w-full mx-4">
      <h3 className="text-xl font-bold text-white mb-4">{title}</h3>
      <p className="text-gray-300 mb-6">{message}</p>
      <div className="flex gap-4">
        <button
          onClick={onCancel}
          className="flex-1 bg-gray-600 hover:bg-gray-700 transition text-white font-semibold py-2 px-4 rounded-lg"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className={`flex-1 ${isDangerous ? 'bg-alert-red hover:bg-red-700' : 'bg-amber hover:bg-amber/80'} transition ${isDangerous ? 'text-white' : 'text-navy'} font-semibold py-2 px-4 rounded-lg`}
        >
          {isDangerous ? 'Delete' : 'Confirm'}
        </button>
      </div>
    </div>
  </div>
);

export default { OllamaInsightBox, ExportButton, LoadingSpinner, ErrorMessage, ConfirmDialog };
