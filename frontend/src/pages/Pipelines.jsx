import React, { useState, useEffect } from 'react';
import { Play, Pause, RefreshCw, AlertCircle, CheckCircle, Clock, GitBranch, Settings, Plus } from 'lucide-react';

const Pipelines = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/pipelines');
      const data = await response.json();
      setPipelines(data.items || []);
    } catch (error) {
      console.error('Failed to fetch pipelines:', error);
      // Mock data
      setPipelines([
        {
          id: 1,
          name: 'IFC Processing Pipeline',
          description: 'Automated IFC file parsing and BIM data extraction',
          status: 'running',
          last_run: new Date().toISOString(),
          duration: '2m 15s',
          success_rate: 98.5,
          stages: [
            { name: 'Upload', status: 'success', duration: '10s' },
            { name: 'Parse IFC', status: 'running', duration: '1m 30s' },
            { name: 'Extract Data', status: 'pending', duration: null },
            { name: 'Generate Report', status: 'pending', duration: null },
          ],
        },
        {
          id: 2,
          name: 'Document Processing',
          description: 'OCR and NLP processing for construction documents',
          status: 'success',
          last_run: new Date(Date.now() - 3600000).toISOString(),
          duration: '5m 42s',
          success_rate: 95.2,
          stages: [
            { name: 'Document Upload', status: 'success', duration: '5s' },
            { name: 'OCR Processing', status: 'success', duration: '3m 20s' },
            { name: 'NLP Analysis', status: 'success', duration: '2m 10s' },
            { name: 'Store Results', status: 'success', duration: '7s' },
          ],
        },
        {
          id: 3,
          name: 'Cost Estimation',
          description: 'Automated cost estimation from BIM models',
          status: 'failed',
          last_run: new Date(Date.now() - 7200000).toISOString(),
          duration: '1m 5s',
          success_rate: 87.3,
          stages: [
            { name: 'Load BIM Model', status: 'success', duration: '15s' },
            { name: 'Extract Quantities', status: 'success', duration: '30s' },
            { name: 'Calculate Costs', status: 'failed', duration: '20s' },
            { name: 'Generate Report', status: 'skipped', duration: null },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-gray-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[status] || colors.pending;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">CI/CD Pipelines</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage automated workflows for data processing and deployments
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Plus className="w-5 h-5" />
          New Pipeline
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Pipelines</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {pipelines.length}
              </p>
            </div>
            <GitBranch className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Running</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {pipelines.filter(p => p.status === 'running').length}
              </p>
            </div>
            <RefreshCw className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {pipelines.length > 0
                  ? Math.round(pipelines.reduce((sum, p) => sum + p.success_rate, 0) / pipelines.length)
                  : 0}%
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {pipelines.filter(p => p.status === 'failed').length}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Pipelines List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-2 text-center py-12 text-gray-500 dark:text-gray-400">
            Loading pipelines...
          </div>
        ) : pipelines.length === 0 ? (
          <div className="col-span-2 text-center py-12 text-gray-500 dark:text-gray-400">
            No pipelines found
          </div>
        ) : (
          pipelines.map((pipeline) => (
            <div
              key={pipeline.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow"
            >
              {/* Pipeline Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {pipeline.name}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {pipeline.description}
                    </p>
                  </div>
                  {getStatusIcon(pipeline.status)}
                </div>

                <div className="flex items-center gap-4 mt-4">
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(pipeline.status)}`}>
                    {pipeline.status.toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Last run: {new Date(pipeline.last_run).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Pipeline Stages */}
              <div className="p-6">
                <div className="space-y-3">
                  {pipeline.stages.map((stage, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        {getStatusIcon(stage.status)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {stage.name}
                          </span>
                          {stage.duration && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {stage.duration}
                            </span>
                          )}
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1 mt-1">
                          <div
                            className={`h-1 rounded-full ${
                              stage.status === 'success' ? 'bg-green-500' :
                              stage.status === 'running' ? 'bg-blue-500 animate-pulse' :
                              stage.status === 'failed' ? 'bg-red-500' :
                              'bg-gray-400'
                            }`}
                            style={{
                              width: stage.status === 'success' ? '100%' :
                                     stage.status === 'running' ? '60%' :
                                     stage.status === 'failed' ? '100%' : '0%'
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pipeline Actions */}
                <div className="flex items-center gap-2 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <Play className="w-4 h-4" />
                    Run
                  </button>
                  <button className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Pause className="w-4 h-4" />
                    Pause
                  </button>
                  <button className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <Settings className="w-4 h-4" />
                    Configure
                  </button>
                  <div className="flex-1 text-right">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Success Rate: <span className="font-semibold">{pipeline.success_rate}%</span>
                    </span>
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

export default Pipelines;
