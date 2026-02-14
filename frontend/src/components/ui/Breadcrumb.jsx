// Breadcrumb Navigation - ITEM 55
// Dynamic route-based breadcrumb with clickable ancestors

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const Breadcrumb = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Route name mapping
  const routeNames = {
    'dashboard': 'Dashboard',
    'chat': 'Chat',
    'documents': 'Documents',
    'bim-viewer': 'BIM Viewer',
    'action-items': 'Action Items',
    'economics': 'Economics',
    'quality': 'Quality',
    'vdc': 'VDC',
    'registry': 'Registry',
    'learning': 'Learning',
    'sandbox': 'Sandbox',
    'ml-tinker': 'ML Tinker',
    'pipelines': 'Pipelines',
    'tasks': 'Tasks',
    'audit': 'Audit',
    'analytics': 'Analytics',
    'edge-devices': 'Edge Devices',
    'admin': 'Admin',
    'settings': 'Settings',
  };

  if (pathnames.length === 0) {
    return null; // Don't show breadcrumb on home page
  }

  return (
    <nav className="flex items-center space-x-2 text-sm mb-6">
      {/* Home */}
      <Link
        to="/"
        className="flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
      >
        <Home className="w-4 h-4" />
      </Link>

      {pathnames.map((name, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const displayName = routeNames[name] || name.charAt(0).toUpperCase() + name.slice(1);

        return (
          <React.Fragment key={routeTo}>
            <ChevronRight className="w-4 h-4 text-gray-400" />
            {isLast ? (
              <span className="text-gray-900 dark:text-white font-medium">
                {displayName}
              </span>
            ) : (
              <Link
                to={routeTo}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              >
                {displayName}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumb;
