// Dark Mode Context - ITEM 96: Theme management with system preference
import React, { createContext, useContext, useState, useEffect } from 'react';

const DarkModeContext = createContext(null);

export const useDarkMode = () => {
  const context = useContext(DarkModeContext);
  if (!context) {
    throw new Error('useDarkMode must be used within a DarkModeProvider');
  }
  return context;
};

export const DarkModeProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(() => {
    // Check localStorage first
    const stored = localStorage.getItem('darkMode');
    if (stored !== null) {
      return stored === 'true';
    }

    // Fall back to system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Update class on document element
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Save preference
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  useEffect(() => {
    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      // Only update if user hasn't set a preference
      const stored = localStorage.getItem('darkMode');
      if (stored === null) {
        setDarkMode(e.matches);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggle = () => {
    setDarkMode((prev) => !prev);
  };

  const enable = () => {
    setDarkMode(true);
  };

  const disable = () => {
    setDarkMode(false);
  };

  const reset = () => {
    localStorage.removeItem('darkMode');
    setDarkMode(window.matchMedia('(prefers-color-scheme: dark)').matches);
  };

  const value = {
    darkMode,
    toggle,
    enable,
    disable,
    reset,
  };

  return <DarkModeContext.Provider value={value}>{children}</DarkModeContext.Provider>;
};

export default DarkModeContext;
