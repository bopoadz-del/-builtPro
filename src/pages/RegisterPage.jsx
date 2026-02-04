import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * RegisterPage provides a form for creating a new user.  On submit the
 * entered credentials are sent to /api/auth/register.  On success the
 * user is redirected to the login page.  Any validation or server
 * errors are displayed.
 */
export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) {
          throw new Error(data.detail || 'Registration failed');
      }
      setSuccess(data.message || 'User registered successfully');
      // After short delay redirect to login
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Register</h1>
      {error && <p className="mb-2 text-red-600">{error}</p>}
      {success && <p className="mb-2 text-green-600">{success}</p>}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block mb-1" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full bg-green-600 text-white py-2 rounded hover:bg-green-700"
        >
          Create Account
        </button>
      </form>
    </div>
  );
}