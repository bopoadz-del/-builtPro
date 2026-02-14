import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, CheckCircle, Circle, AlertCircle, Clock, User, MessageSquare } from 'lucide-react';

const ActionItems = () => {
  const [actionItems, setActionItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterSource, setFilterSource] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActionItems();
  }, [filterStatus, filterSource]);

  const fetchActionItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterStatus !== 'all') params.append('status', filterStatus);
      if (filterSource !== 'all') params.append('source', filterSource);

      const response = await fetch(`/api/v1/action-items?${params}`);
      const data = await response.json();
      setActionItems(data.items || []);
    } catch (error) {
      console.error('Failed to fetch action items:', error);
      // Mock data
      setActionItems([
        {
          id: 1,
          title: 'Review structural drawings for Phase 2',
          description: 'Check for compliance with local building codes',
          status: 'open',
          priority: 'high',
          source: 'meeting',
          assignee: 'John Doe',
          created_by: 'Jane Smith',
          due_date: new Date(Date.now() + 86400000).toISOString(),
          created_at: new Date(Date.now() - 3600000).toISOString(),
          meeting: 'Weekly Coordination - Jan 15',
          comments: 2,
        },
        {
          id: 2,
          title: 'Update MEP clash resolution plan',
          description: 'Address 15 clashes found in BIM coordination',
          status: 'in_progress',
          priority: 'high',
          source: 'bim',
          assignee: 'Mike Johnson',
          created_by: 'System',
          due_date: new Date(Date.now() + 172800000).toISOString(),
          created_at: new Date(Date.now() - 7200000).toISOString(),
          comments: 5,
        },
        {
          id: 3,
          title: 'Approve material submittal for concrete',
          description: 'Review and approve concrete mix design',
          status: 'completed',
          priority: 'medium',
          source: 'document',
          assignee: 'Sarah Lee',
          created_by: 'Tom Brown',
          due_date: new Date(Date.now() - 86400000).toISOString(),
          created_at: new Date(Date.now() - 172800000).toISOString(),
          completed_at: new Date(Date.now() - 43200000).toISOString(),
          comments: 1,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = actionItems.filter(item =>
    item.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'in_progress':
        return <Circle className="w-5 h-5 text-blue-600" />;
      case 'blocked':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      open: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      blocked: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    };
    return colors[status] || colors.open;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    };
    return colors[priority] || colors.medium;
  };

  const getSourceBadge = (source) => {
    const badges = {
      meeting: { label: 'Meeting', icon: '👥' },
      bim: { label: 'BIM', icon: '🏗️' },
      document: { label: 'Document', icon: '📄' },
      chat: { label: 'Chat', icon: '💬' },
      manual: { label: 'Manual', icon: '✍️' },
    };
    return badges[source] || badges.manual;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Action Items</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track action items from meetings, BIM coordination, and documents
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Plus className="w-5 h-5" />
          New Action Item
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {actionItems.length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Open</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {actionItems.filter(i => i.status === 'open').length}
              </p>
            </div>
            <Clock className="w-8 h-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">In Progress</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {actionItems.filter(i => i.status === 'in_progress').length}
              </p>
            </div>
            <Circle className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {actionItems.filter(i => i.status === 'completed').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Blocked</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {actionItems.filter(i => i.status === 'blocked').length}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search action items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="blocked">Blocked</option>
            </select>

            <select
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Sources</option>
              <option value="meeting">Meeting</option>
              <option value="bim">BIM</option>
              <option value="document">Document</option>
              <option value="chat">Chat</option>
            </select>

            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <Filter className="w-5 h-5" />
              More
            </button>
          </div>
        </div>
      </div>

      {/* Action Items List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center text-gray-500 dark:text-gray-400">
            Loading action items...
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center text-gray-500 dark:text-gray-400">
            No action items found
          </div>
        ) : (
          filteredItems.map((item) => (
            <div
              key={item.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">
                  {getStatusIcon(item.status)}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {item.title}
                        </h3>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                          {item.status.replace('_', ' ')}
                        </span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(item.priority)}`}>
                          {item.priority}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        {item.description}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Source</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-1">
                        {getSourceBadge(item.source).icon} {getSourceBadge(item.source).label}
                      </p>
                      {item.meeting && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.meeting}</p>
                      )}
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Assignee</p>
                      <div className="flex items-center gap-1 mt-1">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-900 dark:text-white">{item.assignee}</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Due Date</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-1">
                        {new Date(item.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Created</p>
                      <p className="text-sm text-gray-900 dark:text-white mt-1">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">by {item.created_by}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {item.comments} comments
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <button className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
                        View Details
                      </button>
                      <button className="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300">
                        Update Status
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ActionItems;
