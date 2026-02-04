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
          {/* Core navigation links */}
          <Link
            to="/dashboard"
            className={`border-b-2 pb-1 ${activeClass('/dashboard')}`}
          >
            Dashboard
          </Link>
          <Link
            to="/analytics"
            className={`border-b-2 pb-1 ${activeClass('/analytics')}`}
          >
            Analytics
          </Link>
          <Link
            to="/connectors"
            className={`border-b-2 pb-1 ${activeClass('/connectors')}`}
          >
            Connectors
          </Link>
          <Link
            to="/qto"
            className={`border-b-2 pb-1 ${activeClass('/qto')}`}
          >
            QTO
          </Link>
          <Link
            to="/translation"
            className={`border-b-2 pb-1 ${activeClass('/translation')}`}
          >
            Translation
          </Link>
          <Link
            to="/reasoning"
            className={`border-b-2 pb-1 ${activeClass('/reasoning')}`}
          >
            Reasoning
          </Link>
          <Link
            to="/vision"
            className={`border-b-2 pb-1 ${activeClass('/vision')}`}
          >
            Vision
          </Link>
          <Link
            to="/schedule"
            className={`border-b-2 pb-1 ${activeClass('/schedule')}`}
          >
            Schedule
          </Link>
          <Link
            to="/audio"
            className={`border-b-2 pb-1 ${activeClass('/audio')}`}
          >
            Audio
          </Link>
          <Link
            to="/archive"
            className={`border-b-2 pb-1 ${activeClass('/archive')}`}
          >
            Archive
          </Link>
          <Link
            to="/cad"
            className={`border-b-2 pb-1 ${activeClass('/cad')}`}
          >
            CAD
          </Link>
          <Link
            to="/chat"
            className={`border-b-2 pb-1 ${activeClass('/chat')}`}
          >
            Chat
          </Link>
          <Link
            to="/code"
            className={`border-b-2 pb-1 ${activeClass('/code')}`}
          >
            Code
          </Link>
          {/* Authentication links */}
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