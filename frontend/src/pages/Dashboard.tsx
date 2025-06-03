import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import api from '../api/api';
import { UsageStats } from '../types';
import Card from '../components/Card';
import Chart from '../components/Chart';
import { Users, Shield, BarChart, AlertTriangle, AlertCircle, Clock, Code, Activity, Timer, BarChart3 } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showScanDurations, setShowScanDurations] = useState(true);
  const [scanCardMode, setScanCardMode] = useState<'weekly' | 'findings'>('weekly');

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/admin/stats');
        console.log('Admin stats response:', response.data);
        setStats(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch statistics');
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-64px)]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 text-red-700 p-4 rounded-lg">
          {error || 'Failed to load dashboard data'}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4 sm:mb-0">SDK Administration</h1>
        <div className="flex gap-4">
          <Link
            to="/users"
            className="bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 transition-colors"
          >
            Manage Users
          </Link>
          <Link
            to="/versions"
            className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
          >
            Manage SDK Versions
          </Link>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <Card
          title="Total Users"
          value={stats.totalUsers}
          icon={<Users size={24} />}
          className="border-l-4 border-blue-500"
        />
        <Card
          title="Total Scans"
          value={stats.totalScans}
          icon={<Shield size={24} />}
          className="border-l-4 border-indigo-500"
        />
        <Card
          title="Critical Findings"
          value={stats.findings.critical}
          icon={<AlertTriangle size={24} />}
          className="border-l-4 border-red-500"
        />
        <Card
          title="High Findings"
          value={stats.findings.high}
          icon={<AlertCircle size={24} />}
          className="border-l-4 border-yellow-500"
        />
        <Card
          title="Medium Findings"
          value={stats.findings.medium}
          icon={<BarChart size={24} />}
          className="border-l-4 border-orange-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Trends Overview</h2>
          <Chart
            type="line"
            data={stats.trendsData}
            xKey="date"
            yKeys={['scans', 'findings', 'users']}
            height={300}
          />
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">User Growth</h2>
          <Chart
            type="area"
            data={stats.userGrowth}
            xKey="month"
            yKeys={['users', 'activeUsers']}
            colors={['#4F46E5', '#10B981']}
            height={300}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Vulnerability Types</h2>
          <Chart
            type="pie"
            data={stats.vulnerabilityTypes}
            xKey="type"
            yKeys={['count']}
            height={300}
          />
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">
              {scanCardMode === 'weekly' ? 'Scans This Week (by Day)' : 'Findings per Scan'}
            </h2>
            <div className="flex gap-2">
              <button
                className={`border border-gray-300 rounded px-2 py-1 text-xs flex items-center hover:bg-gray-100 transition-colors ${scanCardMode === 'weekly' ? 'bg-indigo-100 font-bold' : ''}`}
                onClick={() => setScanCardMode('weekly')}
                title="Show Weekly Scans"
              >
                <BarChart3 size={16} className="mr-1" />
                Weekly
              </button>
              <button
                className={`border border-gray-300 rounded px-2 py-1 text-xs flex items-center hover:bg-gray-100 transition-colors ${scanCardMode === 'findings' ? 'bg-indigo-100 font-bold' : ''}`}
                onClick={() => setScanCardMode('findings')}
                title="Show Findings per Scan"
              >
                <BarChart3 size={16} className="mr-1" />
                Findings/Scan
              </button>
            </div>
          </div>
          {scanCardMode === 'weekly' ? (
            <Chart
              type="bar"
              data={stats.weeklyScans}
              xKey="day"
              yKeys={['count']}
              colors={['#4F46E5']}
              height={300}
            />
          ) : (
            <Chart
              type="bar"
              data={stats.findingsPerScan}
              xKey="range"
              yKeys={['count']}
              colors={['#10B981']}
              height={300}
            />
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Recent Activity</h2>
          <div className="space-y-4 max-h-80 overflow-y-auto">
            {stats.recentActivity.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
                {activity.type === 'scan' && <Shield size={20} className="text-indigo-600" />}
                {activity.type === 'user_created' && <Users size={20} className="text-blue-600" />}
                {activity.type === 'version_published' && <Code size={20} className="text-green-600" />}
                <div>
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500">
                    {format(new Date(activity.date), 'PPp')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-6">Top Languages</h2>
          <div className="space-y-4">
            {stats.scansByLanguage.map((lang, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center">
                  <Code size={16} className="text-indigo-600 mr-2" />
                  <span className="text-gray-900">{lang.language}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-gray-600 mr-2">{lang.count} scans</span>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-indigo-600 h-2 rounded-full"
                      style={{
                        width: `${(lang.count / Math.max(...stats.scansByLanguage.map(l => l.count))) * 100}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Latest SDK Versions</h2>
            <Link
              to="/versions"
              className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
            >
              View all
            </Link>
          </div>
          <div className="space-y-4">
            {stats.recentActivity
              .filter(activity => activity.type === 'version_published')
              .map((version, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <Code size={20} className="text-green-600" />
                  <div>
                    <p className="text-sm text-gray-900">{version.description}</p>
                    <p className="text-xs text-gray-500">
                      {format(new Date(version.date), 'PPp')}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;