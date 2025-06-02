import React, { useEffect, useState } from 'react';
import api from '../api/api';
import Card from '../components/Card';
import Chart from '../components/Chart';
import { Shield, AlertTriangle, BarChart, Clock, Copy } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface Finding {
  severity: string;
  category?: string;
  [key: string]: any;
}

interface Scan {
  _id: string;
  timestamp: string;
  results: {
    findings: Finding[];
    [key: string]: any;
  };
  [key: string]: any;
}

const UserDashboard: React.FC = () => {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const response = await api.get('/scans');
        setScans(response.data.scans || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch scan data');
        setLoading(false);
      }
    };
    fetchScans();
  }, []);

  // --- Trends Over Time ---
  // Scans per day
  const scansPerDay = scans.reduce((acc, scan) => {
    const day = new Date(scan.timestamp).toLocaleDateString();
    acc[day] = (acc[day] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const scansPerDayData = Object.entries(scansPerDay).map(([date, count]) => ({ date, count }));

  // Vulnerabilities per scan over time
  const vulnsPerScanData = scans.map(scan => ({
    date: new Date(scan.timestamp).toLocaleDateString(),
    findings: scan.results?.findings?.length || 0,
  }));

  // --- Vulnerability Breakdown ---
  // By severity
  const findingsBySeverity = scans.reduce((acc, scan) => {
    (scan.results?.findings || []).forEach((finding: Finding) => {
      const sev = finding.severity?.toLowerCase() || 'unknown';
      acc[sev] = (acc[sev] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);

  // By type/category
  const findingsByCategory = scans.reduce((acc, scan) => {
    (scan.results?.findings || []).forEach((finding: Finding) => {
      const cat = finding.category || 'Unknown';
      acc[cat] = (acc[cat] || 0) + 1;
    });
    return acc;
  }, {} as Record<string, number>);
  const findingsByCategoryData = Object.entries(findingsByCategory).map(([category, count]) => ({ category, count }));

  // --- Recent Activity ---
  const recentScans = [...scans]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5);

  // Get most recent scan
  const mostRecentScan = scans.length > 0 ? [...scans].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0] : null;
  const topIssue = mostRecentScan?.results?.findings?.[0] || null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 text-red-700 p-4 rounded-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Your Scan Dashboard</h1>
      {user?.apiToken && (
        <div className="mb-8 bg-white rounded-lg shadow-md p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div>
            <span className="font-semibold text-gray-700">Your API Token:</span>
            <div className="mt-2 flex items-center gap-2">
              <span className="font-mono bg-gray-100 px-3 py-1 rounded text-gray-800 select-all break-all">{user.apiToken}</span>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(user.apiToken || '');
                  setCopied(true);
                  setTimeout(() => setCopied(false), 1500);
                }}
                className="ml-2 p-1 rounded hover:bg-gray-200 transition-colors"
                title="Copy token"
              >
                <Copy size={18} />
              </button>
              {copied && <span className="text-green-600 text-xs ml-2">Copied!</span>}
            </div>
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card
          title="Total Scans"
          value={scans.length}
          icon={<Shield size={24} />}
          className="border-l-4 border-indigo-500"
        />
        <Card
          title="Critical Findings"
          value={findingsBySeverity['critical'] || 0}
          icon={<AlertTriangle size={24} />}
          className="border-l-4 border-red-500"
        />
        <Card
          title="Medium Findings"
          value={findingsBySeverity['medium'] || 0}
          icon={<BarChart size={24} />}
          className="border-l-4 border-orange-500"
        />
        <Card
          title="Last Scan"
          value={mostRecentScan ? new Date(mostRecentScan.timestamp).toLocaleString() : 'N/A'}
          icon={<Clock size={24} />}
          className="border-l-4 border-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Scans Per Day</h2>
          <Chart
            type="line"
            data={scansPerDayData}
            xKey="date"
            yKeys={['count']}
            height={300}
          />
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Vulnerabilities Per Scan</h2>
          <Chart
            type="line"
            data={vulnsPerScanData}
            xKey="date"
            yKeys={['findings']}
            height={300}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Vulnerabilities by Severity</h2>
          <Chart
            type="pie"
            data={Object.entries(findingsBySeverity).map(([sev, count]) => ({ type: sev, count }))}
            xKey="type"
            yKeys={['count']}
            height={300}
          />
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Vulnerabilities by Type</h2>
          <Chart
            type="bar"
            data={findingsByCategoryData}
            xKey="category"
            yKeys={['count']}
            height={300}
          />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-6">Recent Activity</h2>
        {recentScans.length === 0 ? (
          <p>No recent scans found.</p>
        ) : (
          <ul>
            {recentScans.map(scan => (
              <li key={scan._id} className="mb-2">
                <strong>Date:</strong> {new Date(scan.timestamp).toLocaleString()} |{' '}
                <strong>Findings:</strong> {scan.results?.findings?.length || 0}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default UserDashboard; 