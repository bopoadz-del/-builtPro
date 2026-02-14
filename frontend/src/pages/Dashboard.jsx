// Dashboard Page - ITEM 78
import React from 'react';
import { Activity, Users, FileText, TrendingUp, Clock, AlertCircle } from 'lucide-react';

const Dashboard = () => {
  const stats = [
    { label: 'Active Projects', value: '12', icon: Activity, color: 'blue', trend: '+2 this month' },
    { label: 'Team Members', value: '48', icon: Users, color: 'green', trend: '+5 this month' },
    { label: 'Documents', value: '1,234', icon: FileText, color: 'purple', trend: '+87 this week' },
    { label: 'Budget Usage', value: '68%', icon: TrendingUp, color: 'yellow', trend: 'On track' },
  ];

  const recentActivity = [
    { action: 'IFC model uploaded', project: 'Heritage Quarter', time: '5 min ago', user: 'John Doe' },
    { action: 'Budget updated', project: 'NEOM Tower', time: '1 hour ago', user: 'Jane Smith' },
    { action: 'Document classified', project: 'Metro Extension', time: '2 hours ago', user: 'AI System' },
    { action: 'Task completed', project: 'Heritage Quarter', time: '3 hours ago', user: 'Mike Johnson' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Welcome back! Here's your overview</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          New Project
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg bg-${stat.color}-100 dark:bg-${stat.color}-900/30`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">{stat.trend}</div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {recentActivity.map((activity, idx) => (
            <div key={idx} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{activity.action}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {activity.project} • {activity.user}
                  </p>
                </div>
                <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                  <Clock className="w-4 h-4 mr-1" />
                  {activity.time}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
