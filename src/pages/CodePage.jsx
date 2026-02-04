import React, { useState } from 'react';

/**
 * CodePage provides a simple interface to request code generation from
 * natural language.  Users describe what they want in plain text and
 * the backend returns generated code.  The current implementation uses
 * a stub endpoint that returns a placeholder snippet.
 */
export default function CodePage() {
  const [description, setDescription] = useState('');
  const [generated, setGenerated] = useState('');
  const [error, setError] = useState('');

  const handleGenerate = async (e) => {
    e.preventDefault();
    const desc = description.trim();
    if (!desc) return;
    setError('');
    setGenerated('');
    try {
      // Build query parameter; encode URI component
      const query = new URLSearchParams({ description: desc }).toString();
      const resp = await fetch(`/api/code/generate?${query}`, {
        method: 'POST',
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || 'Code generation failed');
      }
      setGenerated(data.generated_code || JSON.stringify(data));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Code Generation</h1>
      <p className="mb-4 text-gray-700">
        Describe the code you would like to generate. The AI assistant will
        respond with a snippet. In this stub implementation the response
        is a static placeholder.
      </p>
      <form onSubmit={handleGenerate} className="mb-4">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full h-32 border p-2 rounded mb-2"
          placeholder="e.g. a function that adds two numbers"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Generate
        </button>
      </form>
      {error && <p className="text-red-600 mb-2">{error}</p>}
      {generated && (
        <pre className="p-4 border rounded bg-gray-50 overflow-x-auto text-sm">
          {generated}
        </pre>
      )}
    </div>
  );
}