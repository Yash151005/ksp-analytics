import { useState, useEffect, useCallback } from 'react';
import { crimesAPI, criminalsAPI, analyticsAPI, alertsAPI } from '../services/api';

export const useFetch = (fetchFn, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetchFn();
        if (isMounted) {
          setData(response.data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || err.message);
          setData(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, dependencies);

  return { data, loading, error };
};

export const useCrimeData = (params = {}) => {
  const [crimes, setCrimes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCrimes = useCallback(async (filters = params) => {
    try {
      setLoading(true);
      const response = await crimesAPI.list(filters);
      setCrimes(response.data.data);
      setTotal(response.data.total);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCrimes();
  }, [fetchCrimes]);

  return { crimes, total, loading, error, refetch: fetchCrimes };
};

export const useOllamaStream = (apiCall) => {
  const [streamText, setStreamText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);

  const startStream = useCallback(async () => {
    setStreamText('');
    setIsStreaming(true);
    setError(null);

    try {
      const response = await apiCall();
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
              setStreamText(prev => prev + (data.content || ''));
            } catch (e) {
              // Ignore JSON parse errors
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Streaming error');
    } finally {
      setIsStreaming(false);
    }
  }, [apiCall]);

  return { streamText, isStreaming, error, startStream };
};

export const useCriminalNetwork = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNetwork = async () => {
      try {
        setLoading(true);
        const response = await criminalsAPI.getNetwork();
        setNodes(response.data.nodes);
        setLinks(response.data.links);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNetwork();
  }, []);

  return { nodes, links, loading, error };
};

export const useAnalyticsData = () => {
  const [summary, setSummary] = useState(null);
  const [riskScores, setRiskScores] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const [summaryRes, riskRes, hotspotsRes] = await Promise.all([
          crimesAPI.getSummary(30),
          analyticsAPI.getRiskScores(),
          crimesAPI.getHotspots(),
        ]);

        setSummary(summaryRes.data);
        setRiskScores(riskRes.data.data);
        setHotspots(hotspotsRes.data);
        setError(null);
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  return { summary, riskScores, hotspots, loading, error };
};

export const useAlerts = (params = {}) => {
  const [alerts, setAlerts] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAlerts = useCallback(async (filters = params) => {
    try {
      setLoading(true);
      const response = await alertsAPI.list(filters);
      setAlerts(response.data.data);
      setTotal(response.data.total);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return { alerts, total, loading, error, refetch: fetchAlerts };
};

export default useFetch;
