import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/api';
import { Scan } from '../types';
import Table from '../components/Table';
import { Search, Filter } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const uniqueLanguages = (scans: Scan[]) => {
  const langs = new Set<string>();
  scans.forEach(scan => {
    if (scan.language) langs.add(scan.language);
  });
  return Array.from(langs);
};

const ScanHistory: React.FC = () => {
  const [scans, setScans] = useState<Scan[]>([]);
  const [filteredScans, setFilteredScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    language: '',
    dateFrom: '',
    dateTo: '',
    minFindings: '',
    maxFindings: ''
  });
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const fetchScans = async () => {
      try {
        const endpoint = user?.isAdmin ? '/admin/scans' : '/scans';
        const response = await api.get(endpoint);
        const scansData = response.data.scans || [];
        setScans(scansData);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch scan data');
        console.error('[fetchScans] Error during fetch:', err);
        setLoading(false);
      }
    };
    fetchScans();
  }, [user]);

  // Filter scans based on search term and filter options
  useEffect(() => {
    let filtered = scans;

    const term = searchTerm.toLowerCase();
    if (term) {
      filtered = filtered.filter(scan => {
        const scanId = (scan.id || (scan as any)._id || '').toLowerCase();
        const username = ((scan as any).user || (scan as any).username || '').toLowerCase();
        const language = (scan.language || '').toLowerCase();
        return scanId.includes(term) || 
               username.includes(term) || 
               language.includes(term);
      });
    }
    // Language filter
    if (filterOptions.language) {
      filtered = filtered.filter(scan => scan.language === filterOptions.language);
    }
    // Date range filter
    if (filterOptions.dateFrom) {
      filtered = filtered.filter(scan => {
        const d = new Date(scan.date || (scan as any).timestamp || '');
        return d >= new Date(filterOptions.dateFrom);
      });
    }
    if (filterOptions.dateTo) {
      filtered = filtered.filter(scan => {
        const d = new Date(scan.date || (scan as any).timestamp || '');
        return d <= new Date(filterOptions.dateTo);
      });
    }
    // Findings filter
    if (filterOptions.minFindings) {
      filtered = filtered.filter(scan => (Array.isArray(scan.findings) ? scan.findings.length : 0) >= Number(filterOptions.minFindings));
    }
    if (filterOptions.maxFindings) {
      filtered = filtered.filter(scan => (Array.isArray(scan.findings) ? scan.findings.length : 0) <= Number(filterOptions.maxFindings));
    }

    // Sort by date in descending order (newest first)
    filtered = filtered.sort((a, b) => {
      const getDateString = (scan: any) => {
        return scan.date || scan.timestamp || (scan.results && scan.results.timestamp) || '';
      };
      const dateStringA = getDateString(a);
      const dateStringB = getDateString(b);
      const dateA = new Date(dateStringA);
      const dateB = new Date(dateStringB);
      const comparison = dateB.getTime() - dateA.getTime();
      return comparison;
    });

    setFilteredScans(filtered);
  }, [searchTerm, scans, filterOptions, user]);

  const handleRowClick = (id: string) => {
    navigate(`/scans/${id}`);
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilterOptions({ ...filterOptions, [e.target.name]: e.target.value });
  };

  const handleClearFilters = () => {
    setFilterOptions({ language: '', dateFrom: '', dateTo: '', minFindings: '', maxFindings: '' });
  };

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
        <div className="bg-red-100 text-red-700 p-4 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Scan History</h1>
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search size={18} className="text-gray-400" />
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Scan ID, Username, or Language..."
            className="pl-10 w-full py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div className="flex items-center justify-end gap-2">
          <span className="text-gray-500 mr-2">
            Showing {filteredScans.length} of {scans.length} scans
          </span>
          <button
            className="bg-white text-gray-700 border border-gray-300 rounded-md px-4 py-2 flex items-center hover:bg-gray-50"
            onClick={() => setShowFilter(true)}
          >
            <Filter size={16} className="mr-2" />
            <span>Filter</span>
          </button>
        </div>
      </div>
      {showFilter && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Filter Scans</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select
                name="language"
                value={filterOptions.language}
                onChange={handleFilterChange}
                className="w-full border border-gray-300 rounded-md py-2 px-3"
              >
                <option value="">All</option>
                {uniqueLanguages(scans).map(lang => (
                  <option key={lang} value={lang}>{lang}</option>
                ))}
              </select>
            </div>
            <div className="mb-4 flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Date From</label>
                <input
                  type="date"
                  name="dateFrom"
                  value={filterOptions.dateFrom}
                  onChange={handleFilterChange}
                  className="w-full border border-gray-300 rounded-md py-2 px-3"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Date To</label>
                <input
                  type="date"
                  name="dateTo"
                  value={filterOptions.dateTo}
                  onChange={handleFilterChange}
                  className="w-full border border-gray-300 rounded-md py-2 px-3"
                />
              </div>
            </div>
            <div className="mb-4 flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Min Findings</label>
                <input
                  type="number"
                  name="minFindings"
                  value={filterOptions.minFindings}
                  onChange={handleFilterChange}
                  className="w-full border border-gray-300 rounded-md py-2 px-3"
                  min="0"
                />
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Findings</label>
                <input
                  type="number"
                  name="maxFindings"
                  value={filterOptions.maxFindings}
                  onChange={handleFilterChange}
                  className="w-full border border-gray-300 rounded-md py-2 px-3"
                  min="0"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
                onClick={handleClearFilters}
              >
                Clear Filters
              </button>
              <button
                className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
                onClick={() => setShowFilter(false)}
              >
                Apply Filters
              </button>
            </div>
          </div>
        </div>
      )}
      {scans.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <p className="text-gray-600">No scan history found.</p>
        </div>
      ) : (
        <Table
          scans={filteredScans.map(scan => {
            const id = scan.id || (scan as any)._id || '';
            const findings = Array.isArray(scan.findings)
              ? scan.findings
              : (scan as any).results?.findings && Array.isArray((scan as any).results.findings)
                ? (scan as any).results.findings
                : [];
            const date = scan.date || (scan as any).timestamp || '';
            const language = scan.language || 'Unknown';
            const username = (scan as any).user || (scan as any).username || '-';
            return {
              ...scan,
              id,
              findings,
              date,
              language,
              username
            };
          })}
          onRowClick={handleRowClick}
        />
      )}
    </div>
  );
};

export default ScanHistory;