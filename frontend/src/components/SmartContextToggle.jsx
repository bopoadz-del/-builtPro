// Smart Context Toggle - ITEMS 61-65
// Toggle with capacity polling and settings persistence

import React, { useState, useEffect } from 'react';
import { Zap, ZapOff } from 'lucide-react';
import { useSmartContext } from '../hooks/useSmartContext';

const SmartContextToggle = () => {
  const {
    isEnabled,
    capacity,
    loading,
    toggle,
    error
  } = useSmartContext();

  // Get capacity color
  const getCapacityColor = () => {
    if (!capacity) return 'text-gray-400';
    if (capacity >= 50) return 'text-green-500';
    if (capacity >= 20) return 'text-yellow-500';
    return 'text-red-500';
  };

  // Get capacity badge color
  const getBadgeColor = () => {
    if (!capacity) return 'bg-gray-100 text-gray-600';
    if (capacity >= 50) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
    if (capacity >= 20) return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
    return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Toggle Button */}
      <button
        onClick={toggle}
        disabled={loading}
        className={`
          relative inline-flex items-center h-8 rounded-full w-14 transition-colors
          ${isEnabled
            ? 'bg-green-500 hover:bg-green-600'
            : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        title={isEnabled ? 'Smart Context: ON' : 'Smart Context: OFF'}
      >
        <span
          className={`
            inline-block w-6 h-6 transform transition-transform bg-white rounded-full shadow-lg
            ${isEnabled ? 'translate-x-7' : 'translate-x-1'}
          `}
        >
          {isEnabled ? (
            <Zap className="w-4 h-4 text-green-500 m-1" />
          ) : (
            <ZapOff className="w-4 h-4 text-gray-400 m-1" />
          )}
        </span>
      </button>

      {/* Capacity Badge */}
      {isEnabled && capacity !== null && (
        <div
          className={`
            px-2 py-1 rounded text-xs font-medium whitespace-nowrap
            ${getBadgeColor()}
          `}
          title={`Smart Context Capacity: ${capacity}%`}
        >
          <span className="hidden sm:inline">Capacity: </span>
          <span className={getCapacityColor()}>{capacity}%</span>
        </div>
      )}

      {/* Error indicator */}
      {error && (
        <div className="text-xs text-red-500 dark:text-red-400" title={error}>
          ⚠️
        </div>
      )}
    </div>
  );
};

export default SmartContextToggle;
