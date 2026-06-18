import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { analyticsAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage } from '../components/Shared';
import karnatakaBoundaryRaw from '../data/karnatakaBoundary.geojson?raw';

// Fix Leaflet icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Karnataka state boundary from Bharat Maps Admin_Boundary_District State layer.
const karnatakaBoundary = JSON.parse(karnatakaBoundaryRaw);
const karnatakaGeometry = karnatakaBoundary.features[0].geometry;
const KARNATAKA_COORDINATES = karnatakaGeometry.type === 'MultiPolygon'
  ? karnatakaGeometry.coordinates
  : [karnatakaGeometry.coordinates];

const toLeafletRing = (ring) => ring.map(([lng, lat]) => [lat, lng]);
const getBoundaryBounds = (multiPolygon) => {
  let minLat = Infinity;
  let minLng = Infinity;
  let maxLat = -Infinity;
  let maxLng = -Infinity;

  multiPolygon.forEach((polygon) => {
    polygon.forEach((ring) => {
      ring.forEach(([lng, lat]) => {
        minLat = Math.min(minLat, lat);
        minLng = Math.min(minLng, lng);
        maxLat = Math.max(maxLat, lat);
        maxLng = Math.max(maxLng, lng);
      });
    });
  });

  return [[minLat, minLng], [maxLat, maxLng]];
};
const expandBounds = (bounds, latPadding, lngPadding) => [
  [bounds[0][0] - latPadding, bounds[0][1] - lngPadding],
  [bounds[1][0] + latPadding, bounds[1][1] + lngPadding],
];
const KARNATAKA_LATLNG_POLYGONS = KARNATAKA_COORDINATES.map((polygon) => (
  polygon.map(toLeafletRing)
));
const KARNATAKA_MASK_HOLES = KARNATAKA_LATLNG_POLYGONS.map((polygon) => polygon[0]);
const KARNATAKA_BOUNDS = getBoundaryBounds(KARNATAKA_COORDINATES);
const KARNATAKA_VIEW_BOUNDS = expandBounds(KARNATAKA_BOUNDS, 0.45, 0.45);
const KARNATAKA_CENTER = [
  (KARNATAKA_BOUNDS[0][0] + KARNATAKA_BOUNDS[1][0]) / 2,
  (KARNATAKA_BOUNDS[0][1] + KARNATAKA_BOUNDS[1][1]) / 2,
];
const MAP_MASK_BOUNDS = [
  [30, 65],
  [30, 90],
  [5, 90],
  [5, 65],
  [30, 65],
];

const isPointInRing = (lat, lng, ring) => {
  let inside = false;

  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [lngA, latA] = ring[i];
    const [lngB, latB] = ring[j];
    const intersects = ((latA > lat) !== (latB > lat)) &&
      (lng < ((lngB - lngA) * (lat - latA)) / (latB - latA) + lngA);

    if (intersects) inside = !inside;
  }

  return inside;
};

const isInsideKarnatakaBoundary = (lat, lng) => {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
  if (
    lat < KARNATAKA_BOUNDS[0][0] ||
    lat > KARNATAKA_BOUNDS[1][0] ||
    lng < KARNATAKA_BOUNDS[0][1] ||
    lng > KARNATAKA_BOUNDS[1][1]
  ) {
    return false;
  }

  return KARNATAKA_COORDINATES.some((polygon) => {
    const [outerRing, ...holes] = polygon;
    return isPointInRing(lat, lng, outerRing) &&
      !holes.some((hole) => isPointInRing(lat, lng, hole));
  });
};

const MapController = ({ bounds }) => {
  const map = useMap();
  
  useEffect(() => {
    if (map && bounds) {
      const karnatakaBounds = L.latLngBounds(bounds);
      map.setMaxBounds(karnatakaBounds);
      requestAnimationFrame(() => {
        map.invalidateSize();
        map.fitBounds(karnatakaBounds, { padding: [18, 18], animate: false });
      });
    }
  }, [map, bounds]);
  
  return null;
};

const CrimeMarkers = ({ geoData, onCrimeSelect }) => {
  const getIcon = useMemo(() => (severity) => {
    const colors = {
      1: '#16A34A',
      2: '#84CC16',
      3: '#F59E0B',
      4: '#F97316',
      5: '#DC2626',
    };
    const size = 10 + (severity || 3) * 2;
    return L.divIcon({
      html: `<div style="background-color: ${colors[severity] || '#F59E0B'}; width: ${size}px; height: ${size}px; border: 1px solid #000; border-radius: 50%;"></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    });
  }, []);

  if (!geoData?.features?.length) {
    console.log('No features in geoData');
    return null;
  }

  const validMarkers = geoData.features.filter(feature => {
    const coords = feature.geometry?.coordinates;
    if (!coords || coords.length !== 2) return false;
    const [lng, lat] = coords;
    return isInsideKarnatakaBoundary(lat, lng);
  });

  console.log(`Rendering ${validMarkers.length} markers out of ${geoData.features.length} features`);
  console.log('Sample marker coords:', validMarkers.slice(0, 3).map(f => {
    const [lng, lat] = f.geometry.coordinates;
    return { lat, lng };
  }));

  return (
    <>
      {validMarkers.map((feature) => {
        const [lng, lat] = feature.geometry.coordinates;
        return (
          <Marker
            key={`${lng}-${lat}-${feature.properties.id}`}
            position={[lat, lng]}
            icon={getIcon(feature.properties.severity)}
            eventHandlers={{ click: () => onCrimeSelect?.(feature.properties) }}
          >
            <Popup offset={[0, -10]}>
              <div className="text-xs">
                <strong>{feature.properties.crime_id}</strong>
                <br />
                {feature.properties.type}
              </div>
            </Popup>
          </Marker>
        );
      })}
    </>
  );
};

export const CrimeMap = () => {
  const [geoData, setGeoData] = useState(null);
  const [selectedCrime, setSelectedCrime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    crimeType: '',
    severity: '',
    days: 30,
  });

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        setLoading(true);
        const response = await analyticsAPI.getHotspotsMap();
        console.log('Map data received:', response.data);
        setGeoData(response.data);
        setError(null);
      } catch (err) {
        console.error('Map data error:', err);
        setError('Failed to load map data');
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, [filters]);

  if (loading) return <LoadingSpinner text="Loading crime map..." />;
  if (error) return <ErrorMessage title="Map Error" message={error} />;

  return (
    <div className="flex flex-col gap-2 p-4 h-full w-full overflow-hidden">
      <div className="flex-shrink-0">
        <h1 className="text-2xl font-bold text-white">Interactive Crime Map</h1>
        <p className="text-gray-400 text-sm">Geospatial visualization of crime incidents across Karnataka</p>
      </div>

      {/* Filters */}
      <div className="bg-steel-blue rounded-lg p-3 grid grid-cols-1 md:grid-cols-4 gap-3 flex-shrink-0">
        <div>
          <label className="text-gray-300 text-xs block mb-1">Crime Type</label>
          <select
            value={filters.crimeType}
            onChange={(e) => setFilters({ ...filters, crimeType: e.target.value })}
            className="w-full bg-navy text-white px-2 py-1 text-sm rounded border border-gray-600"
          >
            <option value="">All Types</option>
            <option value="theft">Theft</option>
            <option value="assault">Assault</option>
            <option value="fraud">Fraud</option>
            <option value="murder">Murder</option>
            <option value="drugs">Drugs</option>
          </select>
        </div>

        <div>
          <label className="text-gray-300 text-xs block mb-1">Severity</label>
          <select
            value={filters.severity}
            onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
            className="w-full bg-navy text-white px-2 py-1 text-sm rounded border border-gray-600"
          >
            <option value="">All Levels</option>
            <option value="1">Low (1)</option>
            <option value="2">Medium (2)</option>
            <option value="3">High (3)</option>
            <option value="4">Very High (4)</option>
            <option value="5">Critical (5)</option>
          </select>
        </div>

        <div>
          <label className="text-gray-300 text-xs block mb-1">Date Range</label>
          <select
            value={filters.days}
            onChange={(e) => setFilters({ ...filters, days: parseInt(e.target.value) })}
            className="w-full bg-navy text-white px-2 py-1 text-sm rounded border border-gray-600"
          >
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
            <option value="365">Last Year</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={() => window.print()}
            className="w-full bg-amber text-navy hover:bg-opacity-90 transition font-bold py-1 px-3 rounded text-sm"
          >
            📥 Export
          </button>
        </div>
      </div>

      {/* Map - Single instance only */}
      <div className="flex-1 min-h-0 w-full rounded-lg overflow-hidden border border-gray-600">
        {geoData ? (
          <MapContainer
            center={KARNATAKA_CENTER}
            zoom={6}
            minZoom={6}
            maxZoom={12}
            maxBounds={KARNATAKA_VIEW_BOUNDS}
            maxBoundsViscosity={1}
            style={{ width: '100%', height: '100%', background: '#0A1628' }}
          >
            <MapController bounds={KARNATAKA_VIEW_BOUNDS} />
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              bounds={KARNATAKA_VIEW_BOUNDS}
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            <Polygon
              positions={[MAP_MASK_BOUNDS, ...KARNATAKA_MASK_HOLES]}
              pathOptions={{
                fillColor: '#0A1628',
                fillOpacity: 1,
                fillRule: 'evenodd',
                stroke: false,
              }}
              interactive={false}
            />
            <GeoJSON
              data={karnatakaBoundary}
              style={{
                color: '#F59E0B',
                fillColor: '#F59E0B',
                fillOpacity: 0.08,
                weight: 2,
              }}
              interactive={false}
            />
            <CrimeMarkers geoData={geoData} onCrimeSelect={setSelectedCrime} />
          </MapContainer>
        ) : (
          <div className="w-full h-full bg-gray-700 flex items-center justify-center text-white">
            Loading map data...
          </div>
        )}
      </div>

      {/* Bottom section with Legend and Details */}
      <div className="flex-shrink-0 max-h-[200px] overflow-auto space-y-3">
        {/* Legend */}
        <div className="bg-steel-blue rounded-lg p-3">
        <h3 className="text-white font-bold mb-2 text-sm">Severity Legend</h3>
        <div className="grid grid-cols-3 md:grid-cols-5 gap-2 text-xs">
          {[
            { level: 1, color: '#16A34A', label: 'Low' },
            { level: 2, color: '#84CC16', label: 'Med' },
            { level: 3, color: '#F59E0B', label: 'High' },
            { level: 4, color: '#F97316', label: 'V.High' },
            { level: 5, color: '#DC2626', label: 'Crit' },
          ].map((item) => (
            <div key={item.level} className="flex items-center gap-1">
              <div
                className="w-4 h-4 rounded-full border border-black flex-shrink-0"
                style={{ backgroundColor: item.color }}
              ></div>
              <span className="text-gray-300">{item.label}</span>
            </div>
          ))}
        </div>
        </div>

        {/* Selected Crime Details - Compact */}
        {selectedCrime && (
          <div className="bg-steel-blue rounded-lg p-3 text-white text-xs">
            <h3 className="font-bold mb-2">Crime: {selectedCrime.crime_id}</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-gray-400">Type</p>
                <p>{selectedCrime.type}</p>
              </div>
              <div>
                <p className="text-gray-400">Status</p>
                <p>{selectedCrime.status}</p>
              </div>
              <div>
                <p className="text-gray-400">Date</p>
                <p>{selectedCrime.date}</p>
              </div>
              <div>
                <p className="text-gray-400">Severity</p>
                <p>{selectedCrime.severity}/5</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CrimeMap;
