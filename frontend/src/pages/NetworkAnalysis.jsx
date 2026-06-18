import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { criminalsAPI, aiAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage, OllamaInsightBox } from '../components/Shared';
import { RiskScoreBadge } from '../components/Cards';

export const NetworkAnalysis = () => {
  const svgRef = useRef();
  const containerRef = useRef();
  const [networkData, setNetworkData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analysisText, setAnalysisText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [filters, setFilters] = useState({
    minRisk: 20,
    maxRisk: 100,
  });

  useEffect(() => {
    const fetchNetwork = async () => {
      try {
        setLoading(true);
        const response = await criminalsAPI.getNetwork();
        
        // Filter nodes by risk score
        const filteredNodes = response.data.nodes.filter(
          n => n.risk_score >= filters.minRisk && n.risk_score <= filters.maxRisk
        );
        
        const filteredLinks = response.data.links.filter(
          l => filteredNodes.find(n => n.id === l.source) && 
               filteredNodes.find(n => n.id === l.target)
        );
        
        setNetworkData({ nodes: filteredNodes, links: filteredLinks });
        setError(null);
      } catch (err) {
        setError('Failed to load criminal network');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNetwork();
  }, [filters]);

  useEffect(() => {
    if (!networkData || !svgRef.current || !containerRef.current) return;

    // Get actual SVG dimensions from the rendered container
    const width = containerRef.current.offsetWidth || 800;
    const height = containerRef.current.offsetHeight || 600;

    // Clear previous
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const graphPadding = 24;
    const nodeRadius = (node) => 16 + (node.risk_score / 8);
    const clamp = (value, min, max) => {
      if (min > max) return (min + max) / 2;
      return Math.max(min, Math.min(max, value));
    };
    const getNodeBounds = (node) => {
      const radius = nodeRadius(node);
      return {
        minX: graphPadding + radius,
        maxX: width - graphPadding - radius,
        minY: graphPadding + radius,
        maxY: height - graphPadding - radius,
      };
    };
    const constrainNode = (node) => {
      const bounds = getNodeBounds(node);
      node.x = clamp(node.x, bounds.minX, bounds.maxX);
      node.y = clamp(node.y, bounds.minY, bounds.maxY);
    };

    // Initialize node positions to spread them out
    const padding = 100;
    networkData.nodes.forEach((node, index) => {
      if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
        // Distribute nodes in a grid pattern initially
        const cols = Math.ceil(Math.sqrt(networkData.nodes.length));
        const rows = Math.ceil(networkData.nodes.length / cols);
        const col = index % cols;
        const row = Math.floor(index / cols);
        const usableWidth = Math.max(0, width - 2 * padding);
        const usableHeight = Math.max(0, height - 2 * padding);
        node.x = padding + (cols === 1 ? usableWidth / 2 : (col * usableWidth) / (cols - 1)) + (Math.random() * 30 - 15);
        node.y = padding + (rows === 1 ? usableHeight / 2 : (row * usableHeight) / (rows - 1)) + (Math.random() * 30 - 15);
      }

      constrainNode(node);
    });

    // Create simulation with better force configuration
    const simulation = d3.forceSimulation(networkData.nodes)
      .force('link', d3.forceLink(networkData.links)
        .id(d => d.id)
        .distance(120))
      .force('charge', d3.forceManyBody()
        .strength(-150)
        .distanceMax(500))
      .force('center', d3.forceCenter(width / 2, height / 2)
        .strength(0.05))
      .force('collision', d3.forceCollide()
        .radius(d => nodeRadius(d) + 35)
        .strength(0.7))
      .force('x', d3.forceX(width / 2)
        .strength(0.02))
      .force('y', d3.forceY(height / 2)
        .strength(0.02))
      .alphaDecay(0.04)
      .velocityDecay(0.75)
      .stop();

    for (let i = 0; i < 140; i += 1) {
      simulation.tick();
      networkData.nodes.forEach(constrainNode);
    }

    // Create links
    const link = svg.append('g')
      .selectAll('line')
      .data(networkData.links)
      .enter()
      .append('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => d.strength * 3);

    // Create nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(networkData.nodes)
      .enter()
      .append('circle')
      .attr('r', d => nodeRadius(d))
      .attr('fill', d => {
        if (d.risk_score >= 70) return '#DC2626';
        if (d.risk_score >= 40) return '#F59E0B';
        return '#16A34A';
      })
      .attr('stroke', d => d.id === selectedNode?.id ? '#FFF' : '#000')
      .attr('stroke-width', d => d.id === selectedNode?.id ? 3 : 1)
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
      });

    node.append('title')
      .text(d => `${d.name} (Risk: ${d.risk_score})`);

    // Add labels
    const labels = svg.append('g')
      .selectAll('text')
      .data(networkData.nodes)
      .enter()
      .append('text')
      .attr('font-size', '10px')
      .attr('fill', '#fff')
      .attr('text-anchor', 'middle')
      .style('pointer-events', 'none')
      .text(d => d.alias.substring(0, 6));

    const updatePositions = () => {
      networkData.nodes.forEach(constrainNode);

      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      labels
        .attr('x', d => d.x)
        .attr('y', d => d.y + 3);
    };

    updatePositions();

    function dragstarted(event, d) {
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      const bounds = getNodeBounds(d);
      d.fx = clamp(event.x, bounds.minX, bounds.maxX);
      d.fy = clamp(event.y, bounds.minY, bounds.maxY);
      d.x = d.fx;
      d.y = d.fy;
      updatePositions();
    }

    function dragended(event, d) {
      d.fx = null;
      d.fy = null;
      updatePositions();
    }

  }, [networkData, selectedNode]);

  const generateAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisText('');
    try {
      await aiAPI.analyzeNetwork(
        (chunk) => {
          setAnalysisText(prev => prev + chunk);
        },
        (error) => {
          setAnalysisText('Error analyzing network: ' + error.message);
        }
      );
    } catch (err) {
      console.error(err);
      setAnalysisText('Error analyzing network. Check if Ollama is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (loading) return <LoadingSpinner text="Loading criminal network..." />;
  if (error) return <ErrorMessage title="Network Error" message={error} />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Criminal Network Analysis</h1>
        <p className="text-gray-400">Visualize associations between known criminals</p>
      </div>

      {/* Controls */}
      <div className="bg-steel-blue rounded-lg p-4 flex flex-col md:flex-row gap-4 items-center">
        <div>
          <label className="text-gray-300 text-sm block mb-2">Min Risk Score</label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.minRisk}
            onChange={(e) => setFilters({ ...filters, minRisk: parseInt(e.target.value) })}
            className="w-32"
          />
        </div>

        <div>
          <label className="text-gray-300 text-sm block mb-2">Max Risk Score</label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.maxRisk}
            onChange={(e) => setFilters({ ...filters, maxRisk: parseInt(e.target.value) })}
            className="w-32"
          />
        </div>

        <button
          onClick={generateAnalysis}
          disabled={isAnalyzing}
          className="bg-amber text-navy hover:bg-opacity-90 transition disabled:opacity-50 font-bold py-2 px-4 rounded ml-auto"
        >
          🤖 Analyze Network
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Graph */}
        <div ref={containerRef} className="lg:col-span-2 bg-steel-blue rounded-lg overflow-hidden" style={{ height: '600px' }}>
          <svg ref={svgRef} style={{ width: '100%', height: '100%' }} />
        </div>

        {/* Details Panel */}
        <div className="bg-steel-blue rounded-lg p-6 text-white overflow-y-auto" style={{ height: '600px' }}>
          {selectedNode ? (
            <div>
              <h3 className="text-lg font-bold mb-4">{selectedNode.name}</h3>
              
              <div className="space-y-4">
                <div>
                  <p className="text-gray-400 text-sm">Alias</p>
                  <p className="font-mono">{selectedNode.alias}</p>
                </div>

                <div>
                  <p className="text-gray-400 text-sm">Risk Score</p>
                  <RiskScoreBadge score={selectedNode.risk_score} size="lg" />
                </div>

                <div>
                  <p className="text-gray-400 text-sm">Status</p>
                  <p className="font-semibold capitalize">{selectedNode.status}</p>
                </div>

                <div>
                  <p className="text-gray-400 text-sm">Crime Count</p>
                  <p className="text-2xl font-bold text-amber">{selectedNode.crime_count}</p>
                </div>

                <div>
                  <p className="text-gray-400 text-sm">Network Connections</p>
                  <p className="text-2xl font-bold text-safe-green">
                    {networkData.links.filter(l => l.source.id === selectedNode.id || l.target.id === selectedNode.id).length}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-gray-400 italic">
              Click on a node to view details
            </div>
          )}
        </div>
      </div>

      {/* AI Analysis */}
      <OllamaInsightBox
        title="Network Analysis"
        icon="🔍"
        content={analysisText}
        isStreaming={isAnalyzing}
        onGenerate={generateAnalysis}
      />
    </div>
  );
};

export default NetworkAnalysis;
