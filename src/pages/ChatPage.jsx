import React, { useState } from 'react';

/**
 * ChatPage demonstrates a basic chat interface.  Messages typed by the
 * user are sent to the backend /api/chat/send endpoint.  In this
 * stubbed implementation the backend always returns a 501 error, which
 * is caught and displayed.  A full implementation would stream
 * responses from an AI assistant.
 */
export default function ChatPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');

  const handleSend = async (e) => {
    e.preventDefault();
    const content = input.trim();
    if (!content) return;
    // Add user's message to history
    setMessages((prev) => [...prev, { role: 'user', text: content }]);
    setInput('');
    setError('');
    try {
      const resp = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Chat request failed');
      }
      // Append assistant's reply if provided
      if (data.reply) {
        setMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Chat Assistant</h1>
      <p className="mb-4 text-gray-700">
        Enter a message to interact with the AI assistant. Note: this
        endpoint is not implemented and will return a 501 error.
      </p>
      <div className="border rounded p-4 mb-4 h-64 overflow-y-auto bg-gray-50">
        {messages.length === 0 && <p className="text-gray-500">No messages yet</p>}
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <span
              className={
                msg.role === 'user'
                  ? 'inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded'
                  : 'inline-block bg-gray-200 text-gray-800 px-3 py-1 rounded'
              }
            >
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 border p-2 rounded"
          placeholder="Type your message..."
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Send
        </button>
      </form>
      {error && <p className="text-red-600 mt-2">{error}</p>}
    </div>
  );
}