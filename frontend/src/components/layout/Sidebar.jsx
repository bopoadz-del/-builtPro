// Sidebar Component - ITEM 51
// Fixed 240px sidebar with collapsible mobile view

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Shield,
  GitBranch,
  MessageSquare,
  CheckSquare,
  Box,
  DollarSign,
  Zap,
  Database,
  BarChart3,
  Settings,
  Users,
  HardDrive,
  Radio,
  ClipboardCheck,
  Hammer,
  Menu,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

const Sidebar = ({ isOpen, onToggle, isMobile }) => {
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Navigation items (9-layer architecture)
  const navItems = [
    {
      section: 'Core',
      items: [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/chat', icon: MessageSquare, label: 'Chat' },
        { path: '/documents', icon: FileText, label: 'Documents' },
      ]
    },
    {
      section: 'Construction',
      items: [
        { path: '/bim-viewer', icon: Box, label: 'BIM Viewer' },
        { path: '/action-items', icon: CheckSquare, label: 'Action Items' },
        { path: '/economics', icon: DollarSign, label: 'Economics' },
        { path: '/quality', icon: ClipboardCheck, label: 'Quality' },
        { path: '/vdc', icon: Hammer, label: 'VDC' },
      ]
    },
    {
      section: 'AI & Intelligence',
      items: [
        { path: '/registry', icon: Database, label: 'Registry' },
        { path: '/learning', icon: Zap, label: 'Learning' },
        { path: '/sandbox', icon: Box, label: 'Sandbox' },
        { path: '/ml-tinker', icon: GitBranch, label: 'ML Tinker' },
      ]
    },
    {
      section: 'Management',
      items: [
        { path: '/pipelines', icon: GitBranch, label: 'Pipelines' },
        { path: '/tasks', icon: Radio, label: 'Tasks' },
        { path: '/audit', icon: Shield, label: 'Audit' },
        { path: '/analytics', icon: BarChart3, label: 'Analytics' },
      ]
    },
    {
      section: 'System',
      items: [
        { path: '/edge-devices', icon: HardDrive, label: 'Edge Devices' },
        { path: '/admin', icon: Users, label: 'Admin' },
        { path: '/settings', icon: Settings, label: 'Settings' },
      ]
    }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full bg-gray-900 text-white z-50
          transition-all duration-300 ease-in-out
          ${isMobile ? 'lg:relative' : ''}
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${isCollapsed && !isMobile ? 'w-16' : 'w-60'}
        `}
      >
        {/* Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <Box className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold">Cerebrum</span>
            </div>
          )}

          {/* Desktop collapse toggle */}
          {!isMobile && (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1 hover:bg-gray-800 rounded"
            >
              {isCollapsed ? (
                <ChevronRight className="w-5 h-5" />
              ) : (
                <ChevronLeft className="w-5 h-5" />
              )}
            </button>
          )}

          {/* Mobile close button */}
          {isMobile && (
            <button onClick={onToggle} className="p-1 hover:bg-gray-800 rounded lg:hidden">
              <X className="w-6 h-6" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4">
          {navItems.map((section, idx) => (
            <div key={idx} className="mb-6">
              {!isCollapsed && (
                <div className="px-4 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {section.section}
                </div>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.path);

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => isMobile && onToggle()}
                      className={`
                        flex items-center px-4 py-2.5 transition-colors
                        ${active
                          ? 'bg-blue-600 text-white'
                          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                        }
                        ${isCollapsed ? 'justify-center' : 'space-x-3'}
                      `}
                      title={isCollapsed ? item.label : ''}
                    >
                      <Icon className={`${isCollapsed ? 'w-6 h-6' : 'w-5 h-5'} flex-shrink-0`} />
                      {!isCollapsed && (
                        <span className="text-sm font-medium">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer */}
        {!isCollapsed && (
          <div className="p-4 border-t border-gray-800">
            <div className="text-xs text-gray-400">
              <div className="font-semibold">Cerebrum v1.0.0</div>
              <div className="mt-1">© 2026 BuiltPro</div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};

export default Sidebar;
