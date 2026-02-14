// Error Boundary - ITEM 57
// Catches React errors with Sentry reporting

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);

    // TODO: Send to Sentry
    // if (window.Sentry) {
    //   window.Sentry.captureException(error, { extra: errorInfo });
    // }

    this.setState({
      error,
      errorInfo
    });
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <div className="flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>

            <h1 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-2">
              Something went wrong
            </h1>

            <p className="text-gray-600 dark:text-gray-400 text-center mb-6">
              We're sorry, but something unexpected happened. Please try again or contact support if the problem persists.
            </p>

            {this.state.error && (
              <div className="bg-gray-100 dark:bg-gray-700 rounded p-4 mb-6 overflow-auto max-h-40">
                <p className="text-sm font-mono text-red-600 dark:text-red-400">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <div className="flex space-x-4">
              <button
                onClick={this.handleRetry}
                className="flex-1 flex items-center justify-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>

              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-900 dark:text-white px-4 py-2 rounded-lg transition-colors"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
