import React, { useState, useEffect } from 'react';

/**
 * ActionItemsManager - Display and manage extracted action items
 * 
 * Features:
 * - List view with filtering
 * - Priority and category badges
 * - Due date highlighting
 * - Extract from documents
 * - Status tracking
 */

const PriorityBadge = ({ priority }) => {
  const styles = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const icons = {
    critical: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '⚪',
  };

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${styles[priority] || styles.medium}`}>
      {icons[priority]} {priority}
    </span>
  );
};

const CategoryBadge = ({ category }) => {
  const styles = {
    Design: 'bg-purple-100 text-purple-800',
    Procurement: 'bg-blue-100 text-blue-800',
    Construction: 'bg-green-100 text-green-800',
    Safety: 'bg-red-100 text-red-800',
    Quality: 'bg-yellow-100 text-yellow-800',
    Finance: 'bg-emerald-100 text-emerald-800',
    Coordination: 'bg-indigo-100 text-indigo-800',
  };

  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[category] || 'bg-gray-100 text-gray-800'}`}>
      {category}
    </span>
  );
};

const StatusSelect = ({ status, onChange }) => {
  const statuses = ['pending', 'in_progress', 'completed', 'blocked'];
  
  return (
    <select
      value={status}
      onChange={(e) => onChange(e.target.value)}
      className={`rounded-lg border px-2 py-1 text-xs font-medium ${
        status === 'completed' ? 'border-green-300 bg-green-50 text-green-800' :
        status === 'in_progress' ? 'border-blue-300 bg-blue-50 text-blue-800' :
        status === 'blocked' ? 'border-red-300 bg-red-50 text-red-800' :
        'border-gray-300 bg-gray-50 text-gray-800'
      }`}
    >
      {statuses.map(s => (
        <option key={s} value={s}>{s.replace('_', ' ')}</option>
      ))}
    </select>
  );
};

const ActionItemCard = ({ item, onStatusChange, onEdit }) => {
  const isOverdue = item.due_date && new Date(item.due_date) < new Date() && item.status !== 'completed';

  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
      isOverdue ? 'border-l-4 border-l-red-500' : ''
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900">{item.description}</p>
          
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <PriorityBadge priority={item.priority} />
            {item.category && <CategoryBadge category={item.category} />}
            
            {item.assignee && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                {item.assignee}
              </span>
            )}
            
            {item.due_date && (
              <span className={`flex items-center gap-1 text-xs ${isOverdue ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {new Date(item.due_date).toLocaleDateString()}
                {isOverdue && ' (overdue)'}
              </span>
            )}
          </div>

          {item.source && (
            <p className="mt-2 text-xs text-gray-400">
              From: {item.source}
            </p>
          )}
        </div>

        <div className="flex flex-col items-end gap-2">
          <StatusSelect
            status={item.status || 'pending'}
            onChange={(newStatus) => onStatusChange(item.id, newStatus)}
          />
          <button
            onClick={() => onEdit(item)}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Edit
          </button>
        </div>
      </div>
    </div>
  );
};

const ExtractDialog = ({ onClose, onExtract }) => {
  const [text, setText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);

  const handleExtract = async () => {
    if (!text.trim()) return;
    
    setIsExtracting(true);
    try {
      const response = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        onExtract(data.action_items || []);
      }
    } catch (error) {
      console.error('Extraction failed:', error);
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Extract Action Items</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste meeting notes, email, or any text containing action items..."
          rows={10}
          className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-[#a67c52] focus:outline-none"
        />

        <div className="mt-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleExtract}
            disabled={!text.trim() || isExtracting}
            className="rounded-lg bg-[#a67c52] px-4 py-2 text-sm font-medium text-white hover:bg-[#8b6844] disabled:opacity-50"
          >
            {isExtracting ? 'Extracting...' : 'Extract Actions'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default function ActionItemsManager({ projectId }) {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState({ priority: '', category: '', status: '', search: '' });
  const [showExtractDialog, setShowExtractDialog] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Demo data
  useEffect(() => {
    setItems([
      {
        id: '1',
        description: 'Submit revised foundation drawings for approval',
        assignee: 'Ahmed Hassan',
        due_date: '2024-03-25',
        priority: 'high',
        category: 'Design',
        status: 'in_progress',
        source: 'Weekly Progress Meeting #12',
      },
      {
        id: '2',
        description: 'Coordinate steel delivery schedule with supplier',
        assignee: 'Mohammed Ali',
        due_date: '2024-03-22',
        priority: 'critical',
        category: 'Procurement',
        status: 'pending',
        source: 'Email - March 18',
      },
      {
        id: '3',
        description: 'Complete safety inspection for Zone B',
        assignee: 'Sarah Johnson',
        due_date: '2024-03-20',
        priority: 'high',
        category: 'Safety',
        status: 'pending',
        source: 'Site Visit Report',
      },
      {
        id: '4',
        description: 'Review concrete test results',
        assignee: 'John Smith',
        due_date: '2024-03-28',
        priority: 'medium',
        category: 'Quality',
        status: 'completed',
        source: 'QA Meeting',
      },
      {
        id: '5',
        description: 'Update project schedule with revised milestones',
        assignee: 'Lisa Chen',
        due_date: '2024-03-30',
        priority: 'medium',
        category: 'Coordination',
        status: 'pending',
        source: 'PMO Review',
      },
    ]);
  }, []);

  const filteredItems = items.filter(item => {
    if (filter.priority && item.priority !== filter.priority) return false;
    if (filter.category && item.category !== filter.category) return false;
    if (filter.status && item.status !== filter.status) return false;
    if (filter.search) {
      const search = filter.search.toLowerCase();
      return (
        item.description.toLowerCase().includes(search) ||
        (item.assignee && item.assignee.toLowerCase().includes(search))
      );
    }
    return true;
  });

  const handleStatusChange = (id, newStatus) => {
    setItems(items.map(item => 
      item.id === id ? { ...item, status: newStatus } : item
    ));
  };

  const handleExtract = (newItems) => {
    const itemsWithIds = newItems.map((item, idx) => ({
      ...item,
      id: `new-${Date.now()}-${idx}`,
      status: 'pending',
      source: 'Extracted from text',
    }));
    setItems([...itemsWithIds, ...items]);
    setShowExtractDialog(false);
  };

  const priorities = ['critical', 'high', 'medium', 'low'];
  const categories = ['Design', 'Procurement', 'Construction', 'Safety', 'Quality', 'Finance', 'Coordination'];
  const statuses = ['pending', 'in_progress', 'completed', 'blocked'];

  const stats = {
    total: items.length,
    pending: items.filter(i => i.status === 'pending').length,
    overdue: items.filter(i => i.due_date && new Date(i.due_date) < new Date() && i.status !== 'completed').length,
    completed: items.filter(i => i.status === 'completed').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Action Items</h1>
          <p className="text-gray-500">Track and manage project tasks</p>
        </div>
        <button
          onClick={() => setShowExtractDialog(true)}
          className="flex items-center gap-2 rounded-lg bg-[#a67c52] px-4 py-2 font-medium text-white hover:bg-[#8b6844]"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Extract from Text
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
          <p className="text-sm text-gray-500">Total Items</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
          <p className="text-sm text-gray-500">Pending</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-2xl font-bold text-red-600">{stats.overdue}</p>
          <p className="text-sm text-gray-500">Overdue</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
          <p className="text-sm text-gray-500">Completed</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-white p-4">
        <input
          type="text"
          placeholder="Search actions..."
          value={filter.search}
          onChange={(e) => setFilter({ ...filter, search: e.target.value })}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
        />
        
        <select
          value={filter.priority}
          onChange={(e) => setFilter({ ...filter, priority: e.target.value })}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
        >
          <option value="">All Priorities</option>
          {priorities.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          value={filter.category}
          onChange={(e) => setFilter({ ...filter, category: e.target.value })}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
        >
          <option value="">All Categories</option>
          {categories.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select
          value={filter.status}
          onChange={(e) => setFilter({ ...filter, status: e.target.value })}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#a67c52] focus:outline-none"
        >
          <option value="">All Statuses</option>
          {statuses.map(s => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>

        {(filter.priority || filter.category || filter.status || filter.search) && (
          <button
            onClick={() => setFilter({ priority: '', category: '', status: '', search: '' })}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Action Items List */}
      <div className="space-y-3">
        {filteredItems.map(item => (
          <ActionItemCard
            key={item.id}
            item={item}
            onStatusChange={handleStatusChange}
            onEdit={() => {}}
          />
        ))}

        {filteredItems.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
            <p className="text-gray-500">No action items found</p>
          </div>
        )}
      </div>

      {/* Extract Dialog */}
      {showExtractDialog && (
        <ExtractDialog
          onClose={() => setShowExtractDialog(false)}
          onExtract={handleExtract}
        />
      )}
    </div>
  );
}
