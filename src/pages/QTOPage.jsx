import React, { useState } from 'react';

/**
 * QTOPage allows users to build a list of construction elements and
 * calculate total cost based on unit rates.  Users can input a type
 * (e.g. "wall") and quantity; the page then calls the backend QTO
 * endpoint to calculate aggregated costs.  This simplified interface
 * does not support uploading IFC files; it is intended to showcase
 * manual QTO workflows.
 */
export default function QTOPage() {
  const [elements, setElements] = useState([]);
  const [newType, setNewType] = useState('');
  const [newQty, setNewQty] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [rates, setRates] = useState(null);
  const [loadingRates, setLoadingRates] = useState(false);
  const [errorRates, setErrorRates] = useState(null);

  function addElement(e) {
    e.preventDefault();
    if (!newType || !newQty) return;
    setElements([...elements, { type: newType, quantity: parseFloat(newQty) }]);
    setNewType('');
    setNewQty('');
  }

  function removeElement(index) {
    setElements(elements.filter((_, i) => i !== index));
  }

  async function calculateQTO() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/v1/qto/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ elements }),
      });
      if (!res.ok) throw new Error('Failed to calculate QTO');
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchRates() {
    setLoadingRates(true);
    setErrorRates(null);
    try {
      const res = await fetch('/api/v1/qto/rates');
      if (!res.ok) throw new Error('Failed to load default rates');
      const data = await res.json();
      setRates(data);
    } catch (err) {
      console.error(err);
      setErrorRates(err.message);
    } finally {
      setLoadingRates(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Quantity Take‑Off (QTO)</h1>
      <form onSubmit={addElement} className="flex items-end space-x-4 mb-4">
        <div className="flex-1">
          <label htmlFor="type" className="block font-medium mb-1">Element type</label>
          <input
            id="type"
            type="text"
            className="w-full border rounded p-2"
            value={newType}
            onChange={(e) => setNewType(e.target.value)}
            placeholder="e.g. wall"
            required
          />
        </div>
        <div className="w-32">
          <label htmlFor="quantity" className="block font-medium mb-1">Quantity</label>
          <input
            id="quantity"
            type="number"
            step="any"
            className="w-full border rounded p-2"
            value={newQty}
            onChange={(e) => setNewQty(e.target.value)}
            placeholder="e.g. 10"
            required
          />
        </div>
        <button
          type="submit"
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
        >
          Add
        </button>
      </form>
      {elements.length > 0 && (
        <table className="min-w-full border mb-4">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 border-b text-left">#</th>
              <th className="px-4 py-2 border-b text-left">Type</th>
              <th className="px-4 py-2 border-b text-left">Quantity</th>
              <th className="px-4 py-2 border-b"></th>
            </tr>
          </thead>
          <tbody>
            {elements.map((elem, idx) => (
              <tr key={idx} className="odd:bg-white even:bg-gray-50">
                <td className="px-4 py-2 border-b">{idx + 1}</td>
                <td className="px-4 py-2 border-b capitalize">{elem.type}</td>
                <td className="px-4 py-2 border-b">{elem.quantity}</td>
                <td className="px-4 py-2 border-b text-right">
                  <button
                    onClick={() => removeElement(idx)}
                    className="text-red-600 hover:text-red-800"
                    type="button"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="flex items-center space-x-4 mb-6">
        <button
          onClick={calculateQTO}
          disabled={elements.length === 0 || loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Calculating…' : 'Calculate QTO'}
        </button>
        <button
          onClick={fetchRates}
          className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
        >
          View Default Rates
        </button>
      </div>
      {error && <p className="text-red-600 mb-4">{error}</p>}
      {result && (
        <div className="p-4 border rounded bg-gray-50 mb-4">
          <h2 className="font-medium mb-2">Results</h2>
          <p className="mb-1">
            <span className="font-medium">Total cost:</span> {result.currency} {result.total_cost?.toLocaleString()}
          </p>
          <p className="mb-2">
            <span className="font-medium">Elements processed:</span> {result.element_count}
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full border">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 border-b text-left">Element</th>
                  <th className="px-4 py-2 border-b text-left">Count</th>
                  <th className="px-4 py-2 border-b text-left">Quantity</th>
                  <th className="px-4 py-2 border-b text-left">Unit</th>
                  <th className="px-4 py-2 border-b text-left">Rate</th>
                  <th className="px-4 py-2 border-b text-left">Total</th>
                </tr>
              </thead>
              <tbody>
                {(result.items || []).map((item, idx) => (
                  <tr key={idx} className="odd:bg-white even:bg-gray-50">
                    <td className="px-4 py-2 border-b capitalize">{item.element_type}</td>
                    <td className="px-4 py-2 border-b">{item.count}</td>
                    <td className="px-4 py-2 border-b">{item.quantity}</td>
                    <td className="px-4 py-2 border-b">{item.unit}</td>
                    <td className="px-4 py-2 border-b">{item.unit_rate}</td>
                    <td className="px-4 py-2 border-b">{item.total_cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {loadingRates && <p>Loading default rates…</p>}
      {errorRates && <p className="text-red-600 mb-4">{errorRates}</p>}
      {rates && (
        <div className="p-4 border rounded bg-gray-50">
          <h2 className="font-medium mb-2">Default Unit Rates</h2>
          <table className="min-w-full border">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 border-b text-left">Type</th>
                <th className="px-4 py-2 border-b text-left">Rate</th>
                <th className="px-4 py-2 border-b text-left">Unit</th>
                <th className="px-4 py-2 border-b text-left">Description</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(rates.rates || {}).map(([type, info]) => (
                <tr key={type} className="odd:bg-white even:bg-gray-50">
                  <td className="px-4 py-2 border-b capitalize">{type}</td>
                  <td className="px-4 py-2 border-b">{info.rate}</td>
                  <td className="px-4 py-2 border-b">{info.unit}</td>
                  <td className="px-4 py-2 border-b">{info.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}