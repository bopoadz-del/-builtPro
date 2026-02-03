import React, { useState, useRef, useEffect } from 'react';

/**
 * EnhancedChat - AI Chat interface with document citations
 * 
 * Features:
 * - Real-time chat with AI
 * - Document citations with clickable references
 * - Typing indicators
 * - Message actions (copy, cite)
 * - File attachment support
 */

const TypingIndicator = () => (
  <div className="flex items-center gap-1 px-4 py-2">
    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '0ms' }} />
    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '150ms' }} />
    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: '300ms' }} />
  </div>
);

const Citation = ({ citation, onClick }) => (
  <button
    onClick={() => onClick(citation)}
    className="inline-flex items-center gap-1 rounded bg-[#f6efe6] px-2 py-0.5 text-xs text-[#a67c52] hover:bg-[#ebe3d9]"
  >
    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
    {citation.document_name || `Doc ${citation.document_id?.slice(0, 6)}`}
  </button>
);

const CitationPanel = ({ citation, onClose }) => {
  if (!citation) return null;

  return (
    <div className="fixed bottom-20 right-6 w-80 rounded-lg border border-gray-200 bg-white shadow-xl">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h4 className="font-semibold text-gray-900">Source Document</h4>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="p-4">
        <p className="mb-2 font-medium text-gray-900">{citation.document_name}</p>
        {citation.page && (
          <p className="mb-2 text-xs text-gray-500">Page {citation.page}</p>
        )}
        <div className="rounded bg-gray-50 p-3 text-sm text-gray-700">
          "{citation.snippet}"
        </div>
        <div className="mt-3 flex justify-between text-xs text-gray-500">
          <span>Relevance: {Math.round((citation.relevance_score || 0.8) * 100)}%</span>
          <button className="text-[#a67c52] hover:underline">View document</button>
        </div>
      </div>
    </div>
  );
};

const MessageActions = ({ message, onCopy }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };

  return (
    <div className="flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
      <button
        onClick={handleCopy}
        className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        title={copied ? 'Copied!' : 'Copy'}
      >
        {copied ? (
          <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        )}
      </button>
    </div>
  );
};

const Message = ({ message, onCitationClick }) => {
  const isUser = message.role === 'user';

  return (
    <article className={`group flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
        isUser ? 'bg-[#a67c52] text-white' : 'bg-gray-200 text-gray-600'
      }`}>
        {isUser ? (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        )}
      </div>

      {/* Content */}
      <div className={`flex max-w-[75%] flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-[#a67c52] text-white' 
            : 'border border-gray-200 bg-white text-gray-800'
        }`}>
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
          
          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2 border-t border-gray-100 pt-3">
              {message.citations.map((citation, idx) => (
                <Citation
                  key={idx}
                  citation={citation}
                  onClick={onCitationClick}
                />
              ))}
            </div>
          )}
        </div>

        {/* Timestamp and Actions */}
        <div className="mt-1 flex items-center gap-2 text-xs text-gray-400">
          <span>{message.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          {!isUser && <MessageActions message={message} />}
        </div>
      </div>
    </article>
  );
};

const SuggestedQuestions = ({ questions, onSelect }) => (
  <div className="flex flex-wrap gap-2">
    {questions.map((question, idx) => (
      <button
        key={idx}
        onClick={() => onSelect(question)}
        className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 transition-colors hover:border-[#a67c52] hover:bg-[#f6efe6]"
      >
        {question}
      </button>
    ))}
  </div>
);

export default function EnhancedChat({ project, initialMessages = [] }) {
  const [messages, setMessages] = useState(initialMessages.length > 0 ? initialMessages : [
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome! I\'m your Diriyah AI assistant. I can help you with project documents, schedules, and construction queries. How can I assist you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [attachedFile, setAttachedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const suggestedQuestions = [
    'What are the open RFIs for this week?',
    'Summarize the latest progress report',
    'Show me the concrete specification',
    'What\'s the status of Villa 100?',
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (content) => {
    if (!content.trim() && !attachedFile) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          project_id: project,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || data.reply || 'I apologize, but I couldn\'t process your request.',
          citations: data.citations || [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback response
      const fallbackMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I\'m having trouble connecting to the server. Please try again in a moment.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
      setAttachedFile(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
    }
  };

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {/* Project indicator */}
          {project && (
            <div className="mb-6 text-center">
              <span className="rounded-full bg-gray-200 px-3 py-1 text-xs text-gray-600">
                Conversation for {project}
              </span>
            </div>
          )}

          {/* Messages */}
          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
              onCitationClick={setSelectedCitation}
            />
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200">
                <svg className="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="rounded-2xl border border-gray-200 bg-white">
                <TypingIndicator />
              </div>
            </div>
          )}

          {/* Suggested questions (show only at start) */}
          {messages.length === 1 && (
            <div className="mt-8">
              <p className="mb-3 text-center text-sm text-gray-500">Try asking:</p>
              <SuggestedQuestions
                questions={suggestedQuestions}
                onSelect={sendMessage}
              />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
          {/* Attached file preview */}
          {attachedFile && (
            <div className="mb-3 flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-2">
              <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <span className="flex-1 truncate text-sm text-gray-700">{attachedFile.name}</span>
              <button
                type="button"
                onClick={() => setAttachedFile(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          <div className="flex items-end gap-3">
            {/* Attachment button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="rounded-full p-3 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Text input */}
            <div className="relative flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about documents, schedules, or project status..."
                rows={1}
                className="w-full resize-none rounded-2xl border border-gray-300 bg-white px-4 py-3 pr-12 text-sm shadow-sm focus:border-[#a67c52] focus:outline-none"
                style={{ maxHeight: '150px' }}
              />
            </div>

            {/* Send button */}
            <button
              type="submit"
              disabled={isLoading || (!input.trim() && !attachedFile)}
              className="rounded-full bg-[#a67c52] p-3 text-white shadow-sm transition-colors hover:bg-[#8b6844] disabled:opacity-50"
            >
              {isLoading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Citation Panel */}
      <CitationPanel
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}
