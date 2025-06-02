import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/api';
import { Scan, Finding } from '../types';
import VulnerabilityAccordion from '../components/VulnerabilityAccordion';
import { Trash2, ChevronLeft, Code, AlertCircle } from 'lucide-react';

// Severity ordering for sorting
const severityOrder = {
  critical: 1,
  high: 2,
  medium: 3,
  low: 4,
  info: 5
};

const ScanDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [sortedFindings, setSortedFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const response = await api.get(`/admin/scans/${id}`);
        setScan(response.data);
        
        // Sort findings by severity
        const sorted = [...response.data.findings].sort((a, b) => 
          severityOrder[a.severity] - severityOrder[b.severity]
        );
        setSortedFindings(sorted);
        
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch scan details');
        setLoading(false);
      }
    };

    if (id) {
      fetchScan();
    }
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this scan? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    
    try {
      await api.delete(`/scans/${id}`);
      navigate('/scans');
    } catch (err) {
      setError('Failed to delete scan');
      setDeleting(false);
    }
  };

  // Calculate counts by severity
  const getSeverityCounts = () => {
    if (!scan) return null;
    
    const counts: Record<'critical' | 'high' | 'medium' | 'low' | 'info', number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0,
    };
    const validSeverities: (keyof typeof counts)[] = ['critical', 'high', 'medium', 'low', 'info'];
    function isSeverity(sev: string): sev is keyof typeof counts {
      return validSeverities.includes(sev as keyof typeof counts);
    }
    const findingsArr: Finding[] = Array.isArray(scan.findings)
      ? scan.findings
      : Array.isArray((scan as any).results?.findings)
        ? (scan as any).results.findings
        : [];
    findingsArr.forEach((finding: Finding) => {
      const sev = finding.severity.toLowerCase();
      if (isSeverity(sev)) {
        counts[sev as keyof typeof counts]++;
      }
    });
    
    return counts;
  };

  const severityCounts = getSeverityCounts();

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
        <div className="bg-red-100 text-red-700 p-4 rounded-lg flex items-center">
          <AlertCircle size={20} className="mr-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-yellow-100 text-yellow-700 p-4 rounded-lg">
          Scan not found
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/scans" className="text-indigo-600 hover:text-indigo-800 flex items-center">
          <ChevronLeft size={16} className="mr-1" />
          Back to scan history
        </Link>
      </div>
      
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4 sm:mb-0">Scan Details</h1>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors disabled:opacity-70"
        >
          <Trash2 size={16} />
          <span>{deleting ? 'Deleting...' : 'Delete Scan'}</span>
        </button>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Date</h3>
            <p className="mt-1 text-lg font-medium text-gray-900">
              {(() => {
                const dateStr = scan.date || scan.timestamp || (scan as any).results?.timestamp || '';
                const dateObj = dateStr ? new Date(dateStr) : null;
                return dateObj && !isNaN(dateObj.getTime())
                  ? dateObj.toLocaleDateString()
                  : 'N/A';
              })()}
            </p>
            <p className="text-xs text-gray-500 break-all mt-1">ID: {scan.id || (scan as any)._id || ''}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Language</h3>
            <div className="mt-1 flex items-center">
              <Code size={18} className="text-indigo-600 mr-2" />
              <p className="text-lg font-medium text-gray-900">{scan.language}</p>
            </div>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Total Findings</h3>
            <p className="mt-1 text-lg font-medium text-gray-900">
              {scan.findings.length}
            </p>
          </div>
        </div>
        
        {severityCounts && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Severity Breakdown</h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {severityCounts.critical > 0 && (
                <div className="bg-red-100 text-red-800 rounded px-3 py-2 text-center">
                  <span className="block font-bold">{severityCounts.critical}</span>
                  <span className="text-xs uppercase">Critical</span>
                </div>
              )}
              {severityCounts.high > 0 && (
                <div className="bg-orange-100 text-orange-800 rounded px-3 py-2 text-center">
                  <span className="block font-bold">{severityCounts.high}</span>
                  <span className="text-xs uppercase">High</span>
                </div>
              )}
              {severityCounts.medium > 0 && (
                <div className="bg-amber-100 text-amber-800 rounded px-3 py-2 text-center">
                  <span className="block font-bold">{severityCounts.medium}</span>
                  <span className="text-xs uppercase">Medium</span>
                </div>
              )}
              {severityCounts.low > 0 && (
                <div className="bg-blue-100 text-blue-800 rounded px-3 py-2 text-center">
                  <span className="block font-bold">{severityCounts.low}</span>
                  <span className="text-xs uppercase">Low</span>
                </div>
              )}
              {severityCounts.info > 0 && (
                <div className="bg-gray-100 text-gray-800 rounded px-3 py-2 text-center">
                  <span className="block font-bold">{severityCounts.info}</span>
                  <span className="text-xs uppercase">Info</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      <h2 className="text-xl font-semibold mb-4">Findings</h2>
      
      {scan.findings.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-6 text-center">
          <p className="text-gray-600">No findings for this scan.</p>
        </div>
      ) : (
        <div>
          {sortedFindings.map((finding, idx) => (
            <VulnerabilityAccordion key={finding.id || idx} finding={finding} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ScanDetails;