import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import useAuthStore from '../store/authStore';

export const Sidebar = () => {
  const { user, hasPermission } = useAuthStore();
  const [isMobile, setIsMobile] = useState(false);

  const menuItems = [
    { path: '/', icon: '📊', label: 'Dashboard', perm: 'view_crimes' },
    { path: '/map', icon: '🗺️', label: 'Crime Map', perm: 'view_crimes' },
    { path: '/network', icon: '🔗', label: 'Criminal Network', perm: 'view_criminals' },
    { path: '/analytics', icon: '📈', label: 'Analytics', perm: 'view_analytics' },
    { path: '/offenders', icon: '👮', label: 'Repeat Offenders', perm: 'view_criminals' },
    { path: '/alerts', icon: '🚨', label: 'Alerts', perm: 'view_crimes' },
    { path: '/reports', icon: '📄', label: 'Reports', perm: 'view_reports' },
    { path: '/admin', icon: '⚙️', label: 'Admin', perm: 'manage_users' },
  ];

  const filteredItems = menuItems.filter(item => hasPermission(item.perm));

  const getNavItemClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-3 transition ${
      isActive
        ? 'bg-amber text-navy font-bold'
        : 'text-gray-300 hover:bg-steel-blue'
    }`;

  return (
    <>
      {/* Mobile toggle button */}
      <button
        onClick={() => setIsMobile(!isMobile)}
        className="md:hidden fixed top-4 left-4 z-40 bg-steel-blue text-white p-2 rounded"
      >
        ☰
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-screen bg-navy border-r border-steel-blue w-64 transition-transform md:translate-x-0 z-30 overflow-y-auto flex flex-col ${
          isMobile ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <nav className="py-4 flex-1">
          {filteredItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={getNavItemClass}
              onClick={() => setIsMobile(false)}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

      </aside>

      {/* Overlay for mobile */}
      {isMobile && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsMobile(false)}
        />
      )}
    </>
  );
};

export default Sidebar;
