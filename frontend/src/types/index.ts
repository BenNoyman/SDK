// User interface
export interface User {
  id: string;
  username: string;
  email: string;
  createdAt: string;
  lastLogin: string | null;
  scanCount: number;
  apiToken: string;
  status: 'active' | 'suspended';
}

// SDK Version interface
export interface SDKVersion {
  id: string;
  version: string;
  releaseDate: string;
  status: 'draft' | 'published' | 'deprecated';
  downloads: number;
  changelog: string;
}

// API Key interface
export interface APIKey {
  id: string;
  key: string;
  name: string;
  createdAt: string;
  lastUsed: string | null;
  status: 'active' | 'revoked';
  usage: {
    daily: number;
    monthly: number;
    total: number;
  };
}

// Scan interface
export interface Scan {
  id: string;
  userId: string;
  username: string;
  date: string;
  timestamp?: string;
  language: string;
  findings: Finding[];
}

// Finding interface
export interface Finding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  description: string;
  lineNumber: number;
  line?: number;
  suggestion: string;
}

// Usage Statistics
export interface UsageStats {
  totalUsers: number;
  totalScans: number;
  findings: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  scansByLanguage: {
    language: string;
    count: number;
  }[];
  recentActivity: {
    type: 'scan' | 'user_created' | 'version_published';
    description: string;
    date: string;
  }[];
  trendsData: {
    date: string;
    scans: number;
    findings: number;
    users: number;
  }[];
  vulnerabilityTypes: {
    type: string;
    count: number;
  }[];
  userGrowth: {
    month: string;
    users: number;
    activeUsers: number;
  }[];
  scanDurations: {
    range: string;
    count: number;
  }[];
  findingsPerScan: {
    range: string;
    count: number;
  }[];
  scansThisWeek: number;
  weeklyScans: {
    day: string;
    count: number;
  }[];
}