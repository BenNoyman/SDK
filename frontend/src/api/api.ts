import axios from 'axios';
import { SDKVersion, APIKey, UsageStats, User, Scan } from '../types';

// Mock data for demonstration
const mockUsers: User[] = [
  {
    id: '1',
    username: 'developer1',
    email: 'dev1@example.com',
    createdAt: '2024-01-15',
    lastLogin: '2024-03-15',
    scanCount: 45,
    apiToken: 'tk_live_123456789',
    status: 'active'
  },
  {
    id: '2',
    username: 'developer2',
    email: 'dev2@example.com',
    createdAt: '2024-02-01',
    lastLogin: '2024-03-14',
    scanCount: 23,
    apiToken: 'tk_live_987654321',
    status: 'active'
  }
];

const mockVersions: SDKVersion[] = [
  {
    id: '1',
    version: '2.1.0',
    releaseDate: '2024-03-15',
    status: 'published',
    downloads: 15234,
    changelog: '- Added new vulnerability detection patterns\n- Improved performance\n- Bug fixes'
  },
  {
    id: '2',
    version: '2.0.0',
    releaseDate: '2024-02-01',
    status: 'published',
    downloads: 45123,
    changelog: '- Major version update\n- New API endpoints\n- Breaking changes in configuration'
  }
];

const mockUsageStats: UsageStats = {
  totalUsers: 156,
  totalScans: 4567,
  findings: {
    critical: 123,
    high: 456,
    medium: 789,
    low: 1234,
    info: 2345
  },
  scansByLanguage: [
    { language: 'JavaScript', count: 1234 },
    { language: 'Python', count: 987 },
    { language: 'Java', count: 756 },
    { language: 'Go', count: 432 },
    { language: 'Ruby', count: 321 }
  ],
  recentActivity: [
    {
      type: 'scan',
      description: 'New scan completed by developer1',
      date: '2024-03-15T14:30:00Z'
    },
    {
      type: 'user_created',
      description: 'New user registered: developer3',
      date: '2024-03-15T13:45:00Z'
    },
    {
      type: 'version_published',
      description: 'SDK version 2.1.0 published',
      date: '2024-03-15T12:00:00Z'
    }
  ],
  trendsData: [
    { date: '2024-03-09', scans: 145, findings: 567, users: 134 },
    { date: '2024-03-10', scans: 156, findings: 612, users: 138 },
    { date: '2024-03-11', scans: 178, findings: 689, users: 142 },
    { date: '2024-03-12', scans: 189, findings: 723, users: 145 },
    { date: '2024-03-13', scans: 203, findings: 756, users: 149 },
    { date: '2024-03-14', scans: 234, findings: 845, users: 152 },
    { date: '2024-03-15', scans: 256, findings: 912, users: 156 }
  ],
  vulnerabilityTypes: [
    { type: 'SQL Injection', count: 234 },
    { type: 'XSS', count: 189 },
    { type: 'CSRF', count: 156 },
    { type: 'Authentication', count: 145 },
    { type: 'Authorization', count: 123 }
  ],
  userGrowth: [
    { month: '2023-10', users: 89, activeUsers: 67 },
    { month: '2023-11', users: 102, activeUsers: 78 },
    { month: '2023-12', users: 118, activeUsers: 89 },
    { month: '2024-01', users: 134, activeUsers: 98 },
    { month: '2024-02', users: 145, activeUsers: 112 },
    { month: '2024-03', users: 156, activeUsers: 123 }
  ],
  scanDurations: [
    { range: '0-1 min', count: 234 },
    { range: '1-2 min', count: 567 },
    { range: '2-5 min', count: 789 },
    { range: '5-10 min', count: 345 },
    { range: '10+ min', count: 123 }
  ]
};

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
});

// Add request interceptor for auth (optional, for admin JWT)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Mock API responses
const mockApi = {
  get: async (url: string) => {
    await new Promise(resolve => setTimeout(resolve, 500));

    if (url === '/users') {
      return { data: mockUsers };
    }
    
    if (url === '/versions') {
      return { data: mockVersions };
    }
    
    if (url === '/stats') {
      return { data: mockUsageStats };
    }
    
    throw new Error('Not found');
  },
  
  post: async (url: string, data: any) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { data };
  },
  
  put: async (url: string, data: any) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { data };
  },
  
  delete: async (url: string) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return { data: { success: true } };
  }
};

export default api;