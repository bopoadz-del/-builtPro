import React, { useState, useEffect, useRef } from 'react';
import { Send, Paperclip, Smile, MoreVertical, Search, Phone, Video, Brain, Zap } from 'lucide-react';
import { useSmartContext } from '../hooks/useSmartContext';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const { isEnabled: smartContextEnabled, capacity } = useSmartContext();

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.id);
    }
  }, [selectedConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversations = async () => {
    try {
      const response = await fetch('/api/v1/chat/conversations');
      const data = await response.json();
      setConversations(data.items || []);
      if (data.items && data.items.length > 0) {
        setSelectedConversation(data.items[0]);
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      // Mock data
      const mockConversations = [
        {
          id: 1,
          name: 'Project Team',
          type: 'group',
          unread: 3,
          last_message: 'Let me check the BIM model...',
          last_message_time: new Date().toISOString(),
          participants: 5,
        },
        {
          id: 2,
          name: 'John Doe',
          type: 'direct',
          unread: 0,
          last_message: 'Thanks for the update!',
          last_message_time: new Date(Date.now() - 3600000).toISOString(),
          participants: 1,
        },
        {
          id: 3,
          name: 'AI Assistant',
          type: 'ai',
          unread: 0,
          last_message: 'I can help you with that.',
          last_message_time: new Date(Date.now() - 7200000).toISOString(),
          participants: 1,
        },
      ];
      setConversations(mockConversations);
      setSelectedConversation(mockConversations[0]);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      const response = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`);
      const data = await response.json();
      setMessages(data.items || []);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
      // Mock data
      setMessages([
        {
          id: 1,
          sender: 'Jane Smith',
          sender_id: 2,
          content: 'Has anyone reviewed the structural drawings yet?',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          is_mine: false,
        },
        {
          id: 2,
          sender: 'You',
          sender_id: 1,
          content: 'Yes, I just finished reviewing them. Found a few issues with the foundation details.',
          timestamp: new Date(Date.now() - 3000000).toISOString(),
          is_mine: true,
        },
        {
          id: 3,
          sender: 'Mike Johnson',
          sender_id: 3,
          content: 'Can you share those findings? I\'ll add them to the coordination log.',
          timestamp: new Date(Date.now() - 2400000).toISOString(),
          is_mine: false,
        },
        {
          id: 4,
          sender: 'You',
          sender_id: 1,
          content: 'Sure, uploading the marked-up drawings now.',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          is_mine: true,
          has_attachment: true,
        },
        {
          id: 5,
          sender: 'AI Assistant',
          sender_id: 'ai',
          content: 'I analyzed the structural drawings and found 3 potential conflicts with MEP systems. Would you like me to create action items for the team?',
          timestamp: new Date(Date.now() - 600000).toISOString(),
          is_mine: false,
          is_ai: true,
          smart_context_used: true,
        },
      ]);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !selectedConversation) return;

    const newMessage = {
      id: Date.now(),
      sender: 'You',
      sender_id: 1,
      content: inputMessage,
      timestamp: new Date().toISOString(),
      is_mine: true,
    };

    setMessages([...messages, newMessage]);
    setInputMessage('');

    try {
      // Simulate AI response if talking to AI or if Smart Context is enabled
      if (selectedConversation.type === 'ai' || smartContextEnabled) {
        setIsTyping(true);
        setTimeout(() => {
          const aiResponse = {
            id: Date.now() + 1,
            sender: 'AI Assistant',
            sender_id: 'ai',
            content: generateAIResponse(inputMessage),
            timestamp: new Date().toISOString(),
            is_mine: false,
            is_ai: true,
            smart_context_used: smartContextEnabled,
          };
          setMessages(prev => [...prev, aiResponse]);
          setIsTyping(false);
        }, 1500);
      }

      await fetch(`/api/v1/chat/conversations/${selectedConversation.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: inputMessage }),
      });
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const generateAIResponse = (query) => {
    const responses = {
      default: "I'm analyzing your request with the current project context. How can I assist you further?",
      bim: "I've reviewed the BIM model and identified several optimization opportunities. Would you like me to create a detailed report?",
      cost: "Based on the current project data, I can provide cost estimates and budget analysis. What specific area are you interested in?",
      schedule: "I can help you optimize the project schedule. The critical path currently shows some potential delays in Phase 2.",
    };

    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('bim') || lowerQuery.includes('model')) return responses.bim;
    if (lowerQuery.includes('cost') || lowerQuery.includes('budget')) return responses.cost;
    if (lowerQuery.includes('schedule') || lowerQuery.includes('timeline')) return responses.schedule;
    return responses.default;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex gap-6">
      {/* Conversations Sidebar */}
      <div className="w-80 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col">
        {/* Search */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search conversations..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => setSelectedConversation(conv)}
              className={`p-4 border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors ${
                selectedConversation?.id === conv.id
                  ? 'bg-blue-50 dark:bg-blue-900/20'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <div className="flex items-start justify-between mb-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {conv.name}
                  </h3>
                  {conv.type === 'ai' && (
                    <Brain className="w-4 h-4 text-purple-600" />
                  )}
                </div>
                {conv.unread > 0 && (
                  <span className="px-2 py-1 text-xs bg-blue-600 text-white rounded-full">
                    {conv.unread}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {conv.last_message}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {new Date(conv.last_message_time).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow flex flex-col">
        {/* Chat Header */}
        {selectedConversation && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div>
                <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  {selectedConversation.name}
                  {selectedConversation.type === 'ai' && (
                    <Brain className="w-5 h-5 text-purple-600" />
                  )}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedConversation.type === 'group'
                    ? `${selectedConversation.participants} participants`
                    : selectedConversation.type === 'ai'
                    ? 'AI Assistant with Smart Context'
                    : 'Direct message'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {smartContextEnabled && (
                <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200 rounded-full text-sm">
                  <Zap className="w-4 h-4" />
                  Smart Context ON ({capacity}%)
                </div>
              )}
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <Phone className="w-5 h-5" />
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <Video className="w-5 h-5" />
              </button>
              <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                <MoreVertical className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.is_mine ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-md ${message.is_mine ? 'order-2' : 'order-1'}`}>
                {!message.is_mine && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-1">
                    {message.sender}
                    {message.is_ai && <Brain className="w-3 h-3 text-purple-600" />}
                  </p>
                )}
                <div
                  className={`px-4 py-2 rounded-lg ${
                    message.is_mine
                      ? 'bg-blue-600 text-white'
                      : message.is_ai
                      ? 'bg-purple-100 dark:bg-purple-900/20 text-gray-900 dark:text-white border border-purple-300 dark:border-purple-700'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  {message.has_attachment && (
                    <div className="mt-2 p-2 bg-white/20 rounded flex items-center gap-2 text-xs">
                      <Paperclip className="w-3 h-3" />
                      structural-drawings-markup.pdf
                    </div>
                  )}
                  {message.smart_context_used && (
                    <div className="mt-2 flex items-center gap-1 text-xs opacity-75">
                      <Zap className="w-3 h-3" />
                      Smart Context used
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1 px-1">
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-end gap-2">
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Paperclip className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
              <Smile className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              rows="1"
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
