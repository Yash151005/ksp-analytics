import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { ErrorMessage, LoadingSpinner } from '../components/Shared';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuthStore();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(credentials.username, credentials.password);
    if (success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-navy flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-white mb-2">KSP Analytics</h1>
          <p className="text-gray-400">AI-Driven Crime Intelligence Platform</p>
          <p className="text-gray-500 text-sm mt-2">Karnataka State Police</p>
        </div>

        {/* Login Card */}
        <div className="bg-steel-blue rounded-lg shadow-xl p-8">
          {error && (
            <div className="mb-6 bg-alert-red/20 border border-alert-red rounded p-3">
              <p className="text-alert-red text-sm font-semibold">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-gray-300 text-sm font-bold mb-2">
                Username
              </label>
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                disabled={isLoading}
                placeholder="Enter your username"
                className="w-full bg-navy text-white px-4 py-3 rounded border border-gray-600 focus:border-amber focus:outline-none transition disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-gray-300 text-sm font-bold mb-2">
                Password
              </label>
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                disabled={isLoading}
                placeholder="Enter your password"
                className="w-full bg-navy text-white px-4 py-3 rounded border border-gray-600 focus:border-amber focus:outline-none transition disabled:opacity-50"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !credentials.username || !credentials.password}
              className="w-full bg-amber hover:bg-opacity-90 disabled:opacity-50 transition text-navy font-bold py-3 px-4 rounded-lg duration-200"
            >
              {isLoading ? 'Logging in...' : 'Sign In'}
            </button>
          </form>


        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-xs">
          <p>Secure. Encrypted. Confidential.</p>
          <p className="mt-2">© 2026 Karnataka State Police. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
