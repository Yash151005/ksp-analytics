import React, { useState, useEffect } from 'react';
import { adminAPI } from '../services/api';
import { LoadingSpinner, ErrorMessage, ConfirmDialog } from '../components/Shared';

export const Admin = () => {
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewUserForm, setShowNewUserForm] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState(null);

  const [newUserForm, setNewUserForm] = useState({
    username: '',
    email: '',
    full_name: '',
    password: '',
    role: 'viewer',
  });

  const [showEditUserForm, setShowEditUserForm] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [editUserForm, setEditUserForm] = useState({
    email: '',
    full_name: '',
    role: 'viewer',
    is_active: true,
    password: '',
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [usersRes, logsRes, healthRes] = await Promise.all([
          adminAPI.listUsers({ limit: 100 }),
          adminAPI.listAuditLogs({ limit: 50, days: 7 }),
          adminAPI.getSystemHealth(),
        ]);

        setUsers(usersRes.data.data);
        setAuditLogs(logsRes.data.data);
        setSystemHealth(healthRes.data);
        setError(null);
      } catch (err) {
        setError('Failed to load admin data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleCreateUser = async () => {
    try {
      const response = await adminAPI.createUser(newUserForm);
      setUsers([...users, response.data]);
      setNewUserForm({
        username: '',
        email: '',
        full_name: '',
        password: '',
        role: 'viewer',
      });
      setShowNewUserForm(false);
    } catch (err) {
      alert('Failed to create user: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateUser = async () => {
    try {
      const updateData = { ...editUserForm };
      if (!updateData.password) {
        delete updateData.password;
      }
      const response = await adminAPI.updateUser(editingUserId, updateData);
      setUsers(users.map(u => u.id === editingUserId ? response.data : u));
      setShowEditUserForm(false);
      setEditingUserId(null);
    } catch (err) {
      alert('Failed to update user: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteUser = async (userId) => {
    try {
      await adminAPI.deleteUser(userId);
      setUsers(users.filter(u => u.id !== userId));
      setShowConfirm(false);
    } catch (err) {
      alert('Failed to delete user');
    }
  };

  if (loading) return <LoadingSpinner text="Loading admin panel..." />;
  if (error) return <ErrorMessage title="Admin Error" message={error} />;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-white">Administration Panel</h1>
        <p className="text-gray-400">User management, audit logs, and system health</p>
      </div>

      {/* System Health */}
      {systemHealth && (
        <div className="bg-steel-blue rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded ${systemHealth.database.status === 'healthy' ? 'bg-safe-green/20 border border-safe-green' : 'bg-alert-red/20 border border-alert-red'}`}>
              <p className="text-gray-300 text-sm">Database</p>
              <p className="text-xl font-bold text-white capitalize">{systemHealth.database.status}</p>
              <p className="text-gray-400 text-xs mt-1">{systemHealth.database.crime_records} crimes</p>
            </div>
            <div className={`p-4 rounded ${systemHealth.ollama.status === 'ready' ? 'bg-safe-green/20 border border-safe-green' : 'bg-alert-red/20 border border-alert-red'}`}>
              <p className="text-gray-300 text-sm">Ollama AI</p>
              <p className="text-xl font-bold text-white capitalize">{systemHealth.ollama.status}</p>
              <p className="text-gray-400 text-xs mt-1">{systemHealth.ollama.model}</p>
            </div>
            <div className="bg-amber/20 border border-amber p-4 rounded">
              <p className="text-gray-300 text-sm">Active Users</p>
              <p className="text-xl font-bold text-amber">{users.filter(u => u.is_active).length}</p>
            </div>
            <div className="bg-blue-500/20 border border-blue-500 p-4 rounded">
              <p className="text-gray-300 text-sm">Total Records</p>
              <p className="text-xl font-bold text-white">{(systemHealth.database.crime_records + systemHealth.database.criminal_records).toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-600">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 font-bold transition ${activeTab === 'users' ? 'text-amber border-b-2 border-amber' : 'text-gray-400 hover:text-white'}`}
        >
          👥 Users
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-bold transition ${activeTab === 'audit' ? 'text-amber border-b-2 border-amber' : 'text-gray-400 hover:text-white'}`}
        >
          📋 Audit Logs
        </button>
      </div>

      {/* User Management */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <button
            onClick={() => setShowNewUserForm(!showNewUserForm)}
            className="bg-amber text-navy hover:bg-opacity-90 transition font-bold py-2 px-4 rounded"
          >
            {showNewUserForm ? '✕ Close' : '➕ Add New User'}
          </button>

          {showNewUserForm && (
            <div className="bg-steel-blue rounded-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4">Create New User</h3>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Username"
                  value={newUserForm.username}
                  onChange={(e) => setNewUserForm({ ...newUserForm, username: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={newUserForm.email}
                  onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={newUserForm.full_name}
                  onChange={(e) => setNewUserForm({ ...newUserForm, full_name: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={newUserForm.password}
                  onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <select
                  value={newUserForm.role}
                  onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                >
                  <option value="viewer">Viewer</option>
                  <option value="investigator">Investigator</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  onClick={handleCreateUser}
                  className="w-full bg-safe-green hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
                >
                  ✓ Create User
                </button>
              </div>
            </div>
          )}

          {showEditUserForm && (
            <div className="bg-steel-blue rounded-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4">Edit User</h3>
              <div className="space-y-4">
                <input
                  type="email"
                  placeholder="Email"
                  value={editUserForm.email}
                  onChange={(e) => setEditUserForm({ ...editUserForm, email: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={editUserForm.full_name}
                  onChange={(e) => setEditUserForm({ ...editUserForm, full_name: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <input
                  type="password"
                  placeholder="New Password (leave blank to keep current)"
                  value={editUserForm.password}
                  onChange={(e) => setEditUserForm({ ...editUserForm, password: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                />
                <select
                  value={editUserForm.role}
                  onChange={(e) => setEditUserForm({ ...editUserForm, role: e.target.value })}
                  className="w-full bg-navy text-white px-3 py-2 rounded border border-gray-600"
                >
                  <option value="viewer">Viewer</option>
                  <option value="investigator">Investigator</option>
                  <option value="analyst">Analyst</option>
                  <option value="admin">Admin</option>
                </select>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={editUserForm.is_active}
                    onChange={(e) => setEditUserForm({ ...editUserForm, is_active: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <label className="text-white">Active User</label>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleUpdateUser}
                    className="w-full bg-blue-500 hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
                  >
                    ✓ Save Changes
                  </button>
                  <button
                    onClick={() => {
                      setShowEditUserForm(false);
                      setEditingUserId(null);
                    }}
                    className="w-full bg-gray-600 hover:bg-opacity-80 transition text-white font-bold py-2 px-4 rounded"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="bg-steel-blue rounded-lg overflow-x-auto">
            <table className="w-full text-sm text-gray-300">
              <thead className="bg-navy border-b border-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Username</th>
                  <th className="px-4 py-3 text-left font-semibold">Email</th>
                  <th className="px-4 py-3 text-left font-semibold">Role</th>
                  <th className="px-4 py-3 text-left font-semibold">Status</th>
                  <th className="px-4 py-3 text-left font-semibold">Created</th>
                  <th className="px-4 py-3 text-left font-semibold">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-gray-700 hover:bg-navy transition">
                    <td className="px-4 py-3 font-semibold">{user.username}</td>
                    <td className="px-4 py-3">{user.email}</td>
                    <td className="px-4 py-3">
                      <span className="bg-amber text-navy px-2 py-1 rounded text-xs font-semibold">
                        {user.role.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        user.is_active ? 'bg-safe-green text-white' : 'bg-gray-600 text-white'
                      }`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs">{new Date(user.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 flex gap-2">
                      <button
                        onClick={() => {
                          setEditingUserId(user.id);
                          setEditUserForm({
                            email: user.email || '',
                            full_name: user.full_name || '',
                            role: user.role || 'viewer',
                            is_active: user.is_active,
                            password: '',
                          });
                          setShowEditUserForm(true);
                          setShowNewUserForm(false);
                        }}
                        className="bg-blue-500 hover:bg-opacity-80 transition text-white px-3 py-1 rounded text-xs font-semibold"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          setSelectedUserId(user.id);
                          setShowConfirm(true);
                        }}
                        className="bg-alert-red hover:bg-opacity-80 transition text-white px-3 py-1 rounded text-xs font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-steel-blue rounded-lg overflow-x-auto">
          <table className="w-full text-sm text-gray-300">
            <thead className="bg-navy border-b border-gray-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">User ID</th>
                <th className="px-4 py-3 text-left font-semibold">Action</th>
                <th className="px-4 py-3 text-left font-semibold">Resource</th>
                <th className="px-4 py-3 text-left font-semibold">IP Address</th>
                <th className="px-4 py-3 text-left font-semibold">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log, idx) => (
                <tr key={idx} className="border-b border-gray-700 hover:bg-navy transition">
                  <td className="px-4 py-3">{log.user_id}</td>
                  <td className="px-4 py-3 font-mono text-amber">{log.action}</td>
                  <td className="px-4 py-3">{log.resource_type}</td>
                  <td className="px-4 py-3 font-mono text-xs">{log.ip_address || 'N/A'}</td>
                  <td className="px-4 py-3 text-xs">{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showConfirm && (
        <ConfirmDialog
          title="Delete User"
          message="Are you sure? This user will no longer be able to log in."
          onConfirm={() => handleDeleteUser(selectedUserId)}
          onCancel={() => setShowConfirm(false)}
          isDangerous={true}
        />
      )}
    </div>
  );
};

export default Admin;
