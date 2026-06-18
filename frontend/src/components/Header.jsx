import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

export const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: 'bg-alert-red',
      analyst: 'bg-amber',
      investigator: 'bg-steel-blue',
      viewer: 'bg-safe-green',
    };
    return colors[role] || 'bg-gray-500';
  };

  return (
    <header className="bg-navy border-b border-steel-blue sticky top-0 z-50">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-amber rounded-lg flex items-center justify-center">
            <span className="text-navy font-bold text-lg">K</span>
          </div>
          <h1 className="text-xl font-bold text-white">KSP Analytics</h1>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-4">
            <span className="text-gray-300">{user?.full_name}</span>
            <span className={`${getRoleBadgeColor(user?.role)} text-white px-3 py-1 rounded-full text-sm font-semibold`}>
              {user?.role.toUpperCase()}
            </span>
          </div>

          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="text-gray-300 hover:text-white transition"
            >
              ⚙️
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-steel-blue rounded-lg shadow-lg py-2 z-50">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-white hover:bg-navy transition"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
