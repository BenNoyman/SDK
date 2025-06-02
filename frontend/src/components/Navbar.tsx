import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, Shield } from 'lucide-react';

const Navbar: React.FC = () => {
  const { isAuthenticated, logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // If not authenticated, don't render the navbar
  if (!isAuthenticated) return null;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Check if a path is active
  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="bg-indigo-700 text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex flex-col sm:flex-row justify-between items-center">
        <Link to={user?.isAdmin ? "/dashboard" : "/user-dashboard"} className="flex items-center space-x-2 font-bold text-lg mb-3 sm:mb-0">
          <Shield size={24} />
          <span>VulnScan Portal</span>
        </Link>
        <div className="flex items-center space-x-6">
          <Link 
            to={user?.isAdmin ? "/dashboard" : "/user-dashboard"}
            className={`transition-colors ${isActive(user?.isAdmin ? '/dashboard' : '/user-dashboard') 
              ? 'text-white font-medium' 
              : 'text-indigo-200 hover:text-white'}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/scans" 
            className={`transition-colors ${isActive('/scans') 
              ? 'text-white font-medium' 
              : 'text-indigo-200 hover:text-white'}`}
          >
            Scans
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-1 text-indigo-200 hover:text-white transition-colors"
            aria-label="Logout"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;