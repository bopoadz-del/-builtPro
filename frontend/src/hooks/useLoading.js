// Loading States Hook - ITEM 92: Manage loading states easily
import { useState, useCallback } from 'react';

export const useLoading = (initialState = false) => {
  const [loading, setLoading] = useState(initialState);
  const [error, setError] = useState(null);

  const startLoading = useCallback(() => {
    setLoading(true);
    setError(null);
  }, []);

  const stopLoading = useCallback(() => {
    setLoading(false);
  }, []);

  const setLoadingError = useCallback((err) => {
    setError(err);
    setLoading(false);
  }, []);

  const executeAsync = useCallback(async (asyncFn) => {
    try {
      startLoading();
      const result = await asyncFn();
      stopLoading();
      return result;
    } catch (err) {
      setLoadingError(err);
      throw err;
    }
  }, [startLoading, stopLoading, setLoadingError]);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return {
    loading,
    error,
    startLoading,
    stopLoading,
    setLoadingError,
    executeAsync,
    reset,
  };
};

export default useLoading;
