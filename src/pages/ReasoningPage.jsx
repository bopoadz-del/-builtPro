import React, { useState } from 'react';

/**
 * ReasoningPage allows the user to ask a natural language question and
 * receive an answer from the backend.  In the stub implementation
 * the backend echoes back a canned response.  You could replace this
 * with a call to a large language model or a knowledge base.
 */
export default function ReasoningPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await fetch('/api/v1/reasoning/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error('Failed to get answer');
      const data = await res.json();
      setAnswer(data.answer);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Reasoning</h1>
      <form onSubmit={handleAsk} className="space-y-4">
        <div>
          <label htmlFor="question" className="block font-medium mb-1">Ask a question</label>
          <textarea
            id="question"
            className="w-full border rounded p-2"
            rows="3"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            required
          ></textarea>
        </div>
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Ask
        </button>
      </form>
      {loading && <p className="mt-4">Processing…</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {answer && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <p className="font-medium mb-1">Answer:</p>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
}