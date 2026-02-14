// Responsive Utilities - ITEM 97: Breakpoints and responsive helpers
import { useState, useEffect } from 'react';

// Tailwind CSS breakpoints
export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
};

// Check if current width matches a breakpoint
export const useMediaQuery = (query) => {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const media = window.matchMedia(query);
    const listener = (e) => setMatches(e.matches);

    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
};

// Breakpoint hooks
export const useBreakpoint = (breakpoint) => {
  return useMediaQuery(`(min-width: ${breakpoints[breakpoint]}px)`);
};

export const useIsMobile = () => {
  return !useBreakpoint('md');
};

export const useIsTablet = () => {
  const isMd = useBreakpoint('md');
  const isLg = useBreakpoint('lg');
  return isMd && !isLg;
};

export const useIsDesktop = () => {
  return useBreakpoint('lg');
};

// Get current breakpoint
export const useCurrentBreakpoint = () => {
  const is2xl = useBreakpoint('2xl');
  const isXl = useBreakpoint('xl');
  const isLg = useBreakpoint('lg');
  const isMd = useBreakpoint('md');
  const isSm = useBreakpoint('sm');

  if (is2xl) return '2xl';
  if (isXl) return 'xl';
  if (isLg) return 'lg';
  if (isMd) return 'md';
  if (isSm) return 'sm';
  return 'xs';
};

// Window size hook
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState(() => {
    if (typeof window !== 'undefined') {
      return {
        width: window.innerWidth,
        height: window.innerHeight,
      };
    }
    return {
      width: 0,
      height: 0,
    };
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

// Orientation hook
export const useOrientation = () => {
  const { width, height } = useWindowSize();
  return width > height ? 'landscape' : 'portrait';
};

// Touch device detection
export const useIsTouchDevice = () => {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    setIsTouch(
      'ontouchstart' in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0
    );
  }, []);

  return isTouch;
};

// Preferred color scheme
export const usePreferredColorScheme = () => {
  const isDark = useMediaQuery('(prefers-color-scheme: dark)');
  return isDark ? 'dark' : 'light';
};

// Reduced motion preference
export const usePrefersReducedMotion = () => {
  return useMediaQuery('(prefers-reduced-motion: reduce)');
};

// Container query utilities
export const containerQueries = {
  xs: '@container (min-width: 20rem)',
  sm: '@container (min-width: 24rem)',
  md: '@container (min-width: 28rem)',
  lg: '@container (min-width: 32rem)',
  xl: '@container (min-width: 36rem)',
  '2xl': '@container (min-width: 42rem)',
};

// Responsive helper functions
export const getResponsiveValue = (value, breakpoint) => {
  if (typeof value === 'object') {
    const currentBreakpoint = useCurrentBreakpoint();
    const breakpointOrder = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];
    const currentIndex = breakpointOrder.indexOf(currentBreakpoint);

    // Find the largest breakpoint that's smaller than or equal to current
    for (let i = currentIndex; i >= 0; i--) {
      if (value[breakpointOrder[i]] !== undefined) {
        return value[breakpointOrder[i]];
      }
    }

    // If no match found, return default or first value
    return value.default || value[breakpointOrder[0]];
  }

  return value;
};

// Grid column calculator
export const getGridColumns = (totalColumns, breakpoint) => {
  const defaultColumns = {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 5,
    '2xl': 6,
  };

  if (typeof totalColumns === 'object') {
    return totalColumns[breakpoint] || defaultColumns[breakpoint];
  }

  return Math.min(totalColumns, defaultColumns[breakpoint]);
};

export default {
  breakpoints,
  useMediaQuery,
  useBreakpoint,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useCurrentBreakpoint,
  useWindowSize,
  useOrientation,
  useIsTouchDevice,
  usePreferredColorScheme,
  usePrefersReducedMotion,
  containerQueries,
  getResponsiveValue,
  getGridColumns,
};
