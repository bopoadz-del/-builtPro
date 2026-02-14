// TopBar Component - ITEMS 52, 61-65
// Top navigation with Smart Context Toggle, notifications, user menu

import React, { useState } from 'react';
import { Menu, Bell, User, ChevronDown, Search, Sun, Moon, Zap } from 'lucide-react';
import SmartContextToggle from '../SmartContextToggle';

const TopBar = ({ onMenuClick, user, darkMode, onDarkModeToggle }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notifications] = useState([
    { id: 1, text: 'IFC model uploaded successfully', time: '5m ago', unread: true },
    { id: 2, text: 'Budget alert: Over threshold', time: '1h ago', unread: true },
    { id: 3, text: 'New document classified', time: '2h ago', unread: false },
  ]);

  const unreadCount = notifications.filter(n => n.unread).length;

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 lg:px-6">
      {/* Left Section */}
      <div className="flex items-center space-x-4">
        {/* Mobile Menu Button */}
        <button
          onClick={onMenuClick}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg lg:hidden"
        >
          <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
        </button>

        {/* Search Bar */}
        <div className="hidden md:flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 w-80">
          <Search className="w-5 h-5 text-gray-400 mr-2" />
          <input
            type="text"
            placeholder="Search projects, documents..."
            className="bg-transparent border-none outline-none text-sm w-full text-gray-700 dark:text-gray-300 placeholder-gray-400"
          />
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center space-x-2 lg:space-x-4">
        {/* Smart Context Toggle - ITEMS 61-65 */}
        <SmartContextToggle />

        {/* Dark Mode Toggle - ITEM 56 */}
        <button
          onClick={onDarkModeToggle}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {darkMode ? (
            <Sun className="w-5 h-5 text-yellow-500" />
          ) : (
            <Moon className="w-5 h-5 text-gray-600" />
          )}
        </button>

        {/* Notifications - ITEM 59 */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg relative"
          >
            <Bell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowNotifications(false)}
              />
              <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer ${
                        notification.unread ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                      }`}
                    >
                      <p className="text-sm text-gray-900 dark:text-white">{notification.text}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{notification.time}</p>
                    </div>
                  ))}
                </div>
                <div className="p-3 text-center border-t border-gray-200 dark:border-gray-700">
                  <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                    View all notifications
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* User Menu - ITEM 60 */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center space-x-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {user?.name || 'User'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {user?.role || 'Engineer'}
              </p>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-600 dark:text-gray-300 hidden lg:block" />
          </button>

          {/* User Dropdown */}
          {showUserMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowUserMenu(false)}
              />
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <p className="font-semibold text-gray-900 dark:text-white">{user?.name || 'User'}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email || 'user@cerebrum.ai'}</p>
                </div>
                <div className="py-2">
                  <a href="/profile" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                    Profile Settings
                  </a>
                  <a href="/settings" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                    Preferences
                  </a>
                  <a href="/api-keys" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
                    API Keys
                  </a>
                </div>
                <div className="border-t border-gray-200 dark:border-gray-700 py-2">
                  <button
                    onClick={() => {/* Handle logout */}}
                    className="block w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default TopBar;
