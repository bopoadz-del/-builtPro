import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatInput } from '../components/ChatInput';
import { ProjectManager } from '../components/ProjectManager';
import { FilePreview } from '../components/FilePreview';
import {
  FiSettings,
  FiMenu,
  FiPlus,
  FiShield,
  FiMaximize,
  FiMinimize,
  FiSearch,
  FiClock,
  FiEye,
  FiAward,
  FiCpu,
} from 'react-icons/fi';
import toast, { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import apiService from '../services/api';
import type { Project, Message } from '../types';

export const DashboardEnhanced: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [splitScreen, setSplitScreen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Project management
  const [projects, setProjects] = useState<Project[]>([
    {
      id: '1',
      name: 'Sample Project',
      description: 'A sample project to get started',
      conversations: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      color: 'blue',
    },
  ]);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>('1');

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (
    content: string,
    files?: File[],
    useInternet?: boolean
  ) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const attachments = files?.map((file) => ({
        name: file.name,
        size: file.size,
        type: file.type || 'application/octet-stream',
      }));

      const response = await apiService.sendChatMessage({
        message: content,
        project_id: currentProjectId ?? undefined,
        use_internet: useInternet ?? false,
        attachments,
      });

      const replyText =
        response.reply ||
        response.message ||
        response.response ||
        response.content ||
        'No reply received from the backend.';

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: replyText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    } catch (error) {
      toast.error('Failed to send message');
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    toast.success('New conversation started');
  };

  // Project management handlers
  const handleCreateProject = (name: string, description?: string) => {
    const newProject: Project = {
      id: Date.now().toString(),
      name,
      description,
      conversations: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      color: ['blue', 'green', 'purple', 'red', 'yellow', 'pink'][
        Math.floor(Math.random() * 6)
      ],
    };
    setProjects((prev) => [...prev, newProject]);
    setCurrentProjectId(newProject.id);
    toast.success(`Project "${name}" created`);
  };

  const handleDeleteProject = (projectId: string) => {
    setProjects((prev) => prev.filter((p) => p.id !== projectId));
    if (currentProjectId === projectId) {
      setCurrentProjectId(projects[0]?.id || null);
    }
    toast.success('Project deleted');
  };

  const handleRenameProject = (projectId: string, newName: string) => {
    setProjects((prev) =>
      prev.map((p) => (p.id === projectId ? { ...p, name: newName } : p))
    );
    toast.success('Project renamed');
  };

  const filteredMessages = messages.filter((msg) =>
    msg.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-[calc(100vh-64px)] bg-gray-50">
      <Toaster position="top-right" />

      {/* Sidebar */}
      <AnimatePresence>
        {showSidebar && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            className="w-72 bg-white border-r border-gray-200 flex flex-col"
          >
            {/* Sidebar Header */}
            <div className="p-4 border-b border-gray-200">
              <h1 className="text-xl font-bold text-gray-900">ML Framework</h1>
              <p className="text-sm text-gray-500">AI Assistant</p>
            </div>

            {/* New Chat Button */}
            <div className="p-4 border-b border-gray-200">
              <button
                onClick={handleNewChat}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                <FiPlus className="w-5 h-5" />
                New Conversation
              </button>
            </div>

            {/* Project Manager */}
            <div className="flex-1 overflow-hidden">
              <ProjectManager
                projects={projects}
                currentProjectId={currentProjectId}
                onSelectProject={setCurrentProjectId}
                onCreateProject={handleCreateProject}
                onDeleteProject={handleDeleteProject}
                onRenameProject={handleRenameProject}
                onSelectConversation={(id) => toast(`Loading conversation ${id}`)}
              />
            </div>

            {/* User Profile */}
            <div className="p-4 border-t border-gray-200">
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/formulas')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiCpu className="w-4 h-4" />
                  Formula Execution
                </button>
                <button
                  onClick={() => navigate('/admin')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiShield className="w-4 h-4" />
                  Admin Panel
                </button>
                <button
                  onClick={() => navigate('/admin/certifications')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiAward className="w-4 h-4" />
                  Certifications
                </button>
                <button
                  onClick={() => navigate('/auditor')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiEye className="w-4 h-4" />
                  Audit Dashboard
                </button>
                <button
                  onClick={() => toast('Settings coming soon')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <FiSettings className="w-4 h-4" />
                  Settings
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className={`flex-1 flex ${splitScreen ? 'flex-row' : 'flex-col'}`}>
        {/* Chat Area (Left side in split screen) */}
        <div className={`flex flex-col ${splitScreen ? 'w-1/2 border-r border-gray-200' : 'flex-1'}`}>
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-4 py-3">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <FiMenu className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900">AI Chat</h2>
                <p className="text-xs text-gray-500">
                  {messages.length} messages • Split screen {splitScreen ? 'ON' : 'OFF'}
                </p>
              </div>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`p-2 rounded-lg transition-colors ${
                  showHistory ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
                }`}
                title="Toggle history search"
              >
                <FiClock className="w-5 h-5" />
              </button>
              <button
                onClick={() => setSplitScreen(!splitScreen)}
                className={`p-2 rounded-lg transition-colors ${
                  splitScreen ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100'
                }`}
                title="Toggle split screen"
              >
                {splitScreen ? (
                  <FiMinimize className="w-5 h-5" />
                ) : (
                  <FiMaximize className="w-5 h-5" />
                )}
              </button>
            </div>

            {/* Search Bar */}
            {showHistory && (
              <div className="mt-3">
                <div className="relative">
                  <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search conversation history..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto">
            {filteredMessages.length === 0 && !searchQuery ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-md px-4">
                  <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">💬</span>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    Welcome to ML Framework
                  </h3>
                  <p className="text-gray-600 mb-6">
                    Advanced AI chat with multimedia support
                  </p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">📸 Camera & Video</p>
                      <p className="text-gray-500 text-xs mt-1">Capture media</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">🎤 Voice Recording</p>
                      <p className="text-gray-500 text-xs mt-1">Audio messages</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">📦 ZIP/RAR/7Z</p>
                      <p className="text-gray-500 text-xs mt-1">Archive support</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">🗓️ XER/MPP</p>
                      <p className="text-gray-500 text-xs mt-1">Project schedules</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">📐 CAD Files</p>
                      <p className="text-gray-500 text-xs mt-1">DWG, DXF, RVT</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="font-medium text-gray-700">🌐 Internet</p>
                      <p className="text-gray-500 text-xs mt-1">Web search</p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="max-w-4xl mx-auto p-4 space-y-6">
                {searchQuery && filteredMessages.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    No messages found matching "{searchQuery}"
                  </div>
                )}

                {filteredMessages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                        AI
                      </div>
                    )}

                    <div
                      className={`max-w-2xl rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      <p
                        className={`text-xs mt-2 ${
                          message.role === 'user' ? 'text-primary-100' : 'text-gray-400'
                        }`}
                      >
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </p>
                    </div>

                    {message.role === 'user' && (
                      <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                        U
                      </div>
                    )}
                  </motion.div>
                ))}

                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex gap-3 justify-start"
                  >
                    <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold">
                      AI
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: '0.1s' }}
                        />
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: '0.2s' }}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Chat Input */}
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>

        {/* Right Panel (Split Screen View) */}
        {splitScreen && (
          <div className="w-1/2 bg-gray-50 flex items-center justify-center p-8">
            <div className="text-center">
              <div className="w-32 h-32 bg-gray-200 rounded-lg mx-auto mb-4 flex items-center justify-center">
                <FiMaximize className="w-16 h-16 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Extended Workspace
              </h3>
              <p className="text-gray-600 text-sm max-w-md">
                This panel can display file previews, documentation, code editors, or additional
                context while you chat with AI
              </p>
              <p className="text-xs text-gray-500 mt-4">
                Upload a file to see preview here
              </p>
            </div>
          </div>
        )}
      </div>

      {/* File Preview Modal */}
      {selectedFile && (
        <FilePreview file={selectedFile} onClose={() => setSelectedFile(null)} />
      )}
    </div>
  );
};
