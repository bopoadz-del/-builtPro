import React from 'react';
import { Link, useLocation } from 'react-router-dom';

/**
 * Simple navigation bar that appears on all pages.  It highlights the
 * current route and provides links to the login, registration and
 * dashboard pages.  If a user has logged in, their token will be stored
 * in localStorage under the `access_token` key; you can extend this
 * component to display the current user or a logout button.
 */
export default function Navbar() {
  const location = useLocation();
  const activeClass = (path) =>
    location.pathname === path
      ? 'text-blue-600 border-blue-600'
      : 'text-gray-700 border-transparent hover:text-blue-600 hover:border-blue-600';

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="text-xl font-semibold text-gray-800">
          BuiltPro
        </Link>
        <div className="flex space-x-4">
          <Link
            to="/dashboard"
            className={`border-b-2 pb-1 ${activeClass('/dashboard')}`}
          >
            Dashboard
          </Link>
          <Link
            to="/login"
            className={`border-b-2 pb-1 ${activeClass('/login')}`}
          >
            Login
          </Link>
          <Link
            to="/register"
            className={`border-b-2 pb-1 ${activeClass('/register')}`}
          >
            Register
          </Link>
        </div>
      </div>
    </nav>
  );
}