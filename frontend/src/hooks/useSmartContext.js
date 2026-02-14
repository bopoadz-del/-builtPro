// Smart Context Hook - ITEMS 62-64
// Manages Smart Context state with capacity polling and settings persistence

import { useState, useEffect, useCallback, useRef } from 'react';

export const useSmartContext = () => {
  const [isEnabled, setIsEnabled] = useState(() => {
    // Load from localStorage
    const saved = localStorage.getItem('smart_context_enabled');
    return saved === 'true';
  });

  const [capacity, setCapacity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);
  const pollIntervalRef = useRef(null);

  // Fetch capacity from API
  const fetchCapacity = useCallback(async () => {
    if (!isEnabled) return;

    try {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new AbortController
      abortControllerRef.current = new AbortController();

      const response = await fetch('/api/v1/sessions/capacity', {
        signal: abortControllerRef.current.signal,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch capacity');
      }

      const data = await response.json();
      setCapacity(data.capacity || 85); // Default to 85% if not provided
      setError(null);
    } catch (err) {
      if (err.name === 'AbortError') {
        // Request was cancelled, ignore
        return;
      }
      console.error('Capacity fetch error:', err);
      setError('Failed to fetch capacity');
      // Don't set capacity to null on error, keep last known value
    }
  }, [isEnabled]);

  // Start polling when enabled
  useEffect(() => {
    if (isEnabled) {
      // Fetch immediately
      fetchCapacity();

      // Poll every 5 seconds
      pollIntervalRef.current = setInterval(fetchCapacity, 5000);
    } else {
      // Clear capacity when disabled
      setCapacity(null);

      // Clear interval
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }

    // Cleanup on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [isEnabled, fetchCapacity]);

  // Toggle Smart Context
  const toggle = useCallback(async () => {
    setLoading(true);
    setError(null);

    const newValue = !isEnabled;

    try {
      // Persist to backend
      const response = await fetch('/api/v1/settings', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          smart_context_enabled: newValue
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update settings');
      }

      // Update state
      setIsEnabled(newValue);

      // Persist to localStorage
      localStorage.setItem('smart_context_enabled', String(newValue));
    } catch (err) {
      console.error('Toggle error:', err);
      setError('Failed to toggle Smart Context');

      // Rollback on error
      // (don't change isEnabled)
    } finally {
      setLoading(false);
    }
  }, [isEnabled]);

  return {
    isEnabled,
    capacity,
    loading,
    error,
    toggle,
    refresh: fetchCapacity
  };
};
