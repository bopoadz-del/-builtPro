import React, { useState } from 'react';

/**
 * TranslationPage allows a user to input text and translate it into
 * another language.  The backend translation endpoint returns a
 * stubbed result by reversing the text, so this page is primarily
 * illustrative.  You can extend it with additional language options
 * or integrate with a real translation service.
 */
export default function TranslationPage() {
  const [text, setText] = useState('');
  const [targetLang, setTargetLang] = useState('en');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/v1/translation/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, target_language: targetLang }),
      });
      if (!res.ok) throw new Error('Translation failed');
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Translation</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="text" className="block font-medium mb-1">Text to translate</label>
          <textarea
            id="text"
            className="w-full border rounded p-2"
            rows="4"
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
          ></textarea>
        </div>
        <div>
          <label htmlFor="lang" className="block font-medium mb-1">Target language</label>
          <select
            id="lang"
            className="border rounded p-2"
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
          >
            <option value="en">English (en)</option>
            <option value="ar">Arabic (ar)</option>
            <option value="fr">French (fr)</option>
            <option value="es">Spanish (es)</option>
          </select>
        </div>
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Translate
        </button>
      </form>
      {loading && <p className="mt-4">Translating…</p>}
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {result && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <p className="font-medium mb-1">Translated text:</p>
          <p>{result.translated_text}</p>
        </div>
      )}
    </div>
  );
}