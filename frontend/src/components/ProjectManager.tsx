import React, { useState } from 'react';
import { FiPlus, FiTrash2, FiEdit3, FiFolder, FiCheck, FiX } from 'react-icons/fi';
import type { Project } from '../types';

interface ProjectManagerProps {
  projects: Project[];
  currentProjectId: string | null;
  onSelectProject: (id: string) => void;
  onCreateProject: (name: string, description?: string) => void;
  onDeleteProject: (id: string) => void;
  onRenameProject: (id: string, newName: string) => void;
  onSelectConversation: (id: string) => void;
}

const PROJECT_COLORS: Record<string, string> = {
  blue: 'bg-blue-500',
  green: 'bg-green-500',
  purple: 'bg-purple-500',
  red: 'bg-red-500',
  yellow: 'bg-yellow-500',
  pink: 'bg-pink-500',
};

export const ProjectManager: React.FC<ProjectManagerProps> = ({
  projects,
  currentProjectId,
  onSelectProject,
  onCreateProject,
  onDeleteProject,
  onRenameProject,
}) => {
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const handleCreate = () => {
    const trimmed = newProjectName.trim();
    if (!trimmed) return;
    onCreateProject(trimmed);
    setNewProjectName('');
    setShowNewProject(false);
  };

  const handleRename = (id: string) => {
    const trimmed = editName.trim();
    if (!trimmed) return;
    onRenameProject(id, trimmed);
    setEditingId(null);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Projects
        </span>
        <button
          onClick={() => setShowNewProject(!showNewProject)}
          className="p-1 hover:bg-gray-100 rounded transition-colors"
          title="New project"
        >
          <FiPlus className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* New project form */}
      {showNewProject && (
        <div className="px-4 pb-2">
          <input
            type="text"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="Project name..."
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-transparent outline-none"
            autoFocus
          />
          <div className="flex gap-1 mt-1">
            <button
              onClick={handleCreate}
              className="flex-1 text-xs py-1 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
            >
              Create
            </button>
            <button
              onClick={() => {
                setShowNewProject(false);
                setNewProjectName('');
              }}
              className="flex-1 text-xs py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Project list */}
      <div className="flex-1 overflow-y-auto px-2">
        {projects.map((project) => (
          <div
            key={project.id}
            className={`group flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer mb-1 transition-colors ${
              currentProjectId === project.id
                ? 'bg-primary-50 text-primary-700'
                : 'hover:bg-gray-100 text-gray-700'
            }`}
            onClick={() => onSelectProject(project.id)}
          >
            <div
              className={`w-3 h-3 rounded-full flex-shrink-0 ${
                PROJECT_COLORS[project.color || 'blue'] || 'bg-blue-500'
              }`}
            />

            {editingId === project.id ? (
              <div className="flex-1 flex items-center gap-1">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRename(project.id);
                    if (e.key === 'Escape') setEditingId(null);
                  }}
                  className="flex-1 px-1 py-0.5 text-sm border border-gray-300 rounded outline-none"
                  autoFocus
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRename(project.id);
                  }}
                  className="p-0.5 text-green-600 hover:bg-green-50 rounded"
                >
                  <FiCheck className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingId(null);
                  }}
                  className="p-0.5 text-gray-400 hover:bg-gray-100 rounded"
                >
                  <FiX className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <>
                <FiFolder className="w-4 h-4 flex-shrink-0" />
                <span className="flex-1 text-sm truncate">{project.name}</span>
                <div className="hidden group-hover:flex items-center gap-0.5">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingId(project.id);
                      setEditName(project.name);
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    title="Rename"
                  >
                    <FiEdit3 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteProject(project.id);
                    }}
                    className="p-1 hover:bg-red-100 text-red-500 rounded transition-colors"
                    title="Delete"
                  >
                    <FiTrash2 className="w-3 h-3" />
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
