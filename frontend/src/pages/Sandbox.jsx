import React, { useState, useEffect } from 'react';
import { Play, Save, Download, Upload, Code, Terminal, FileCode, Trash2, Copy } from 'lucide-react';

const Sandbox = () => {
  const [code, setCode] = useState('');
  const [output, setOutput] = useState('');
  const [language, setLanguage] = useState('python');
  const [isRunning, setIsRunning] = useState(false);
  const [savedScripts, setSavedScripts] = useState([]);

  useEffect(() => {
    fetchSavedScripts();
    loadDefaultCode();
  }, [language]);

  const loadDefaultCode = () => {
    const templates = {
      python: `# Python Sandbox - Test your BIM processing scripts
import json

def process_ifc_data(data):
    """Example IFC data processing function"""
    print("Processing IFC data...")
    return {"status": "success", "items": len(data)}

# Test data
test_data = [
    {"type": "Wall", "id": "W001"},
    {"type": "Door", "id": "D001"},
]

result = process_ifc_data(test_data)
print(json.dumps(result, indent=2))
`,
      javascript: `// JavaScript Sandbox - Test your frontend logic
console.log("JavaScript Sandbox Ready");

// Example: Calculate project cost
function calculateProjectCost(items) {
  const total = items.reduce((sum, item) => sum + item.cost, 0);
  console.log(\`Total Cost: $\${total.toFixed(2)}\`);
  return total;
}

const projectItems = [
  { name: "Materials", cost: 50000 },
  { name: "Labor", cost: 75000 },
  { name: "Equipment", cost: 25000 }
];

calculateProjectCost(projectItems);
`,
      sql: `-- SQL Sandbox - Test your database queries
-- Example: Get active projects with budget over $100k

SELECT
  p.name,
  p.status,
  p.budget,
  COUNT(t.id) as task_count
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
WHERE p.status = 'active'
  AND p.budget > 100000
GROUP BY p.id, p.name, p.status, p.budget
ORDER BY p.budget DESC
LIMIT 10;
`,
    };
    setCode(templates[language] || '');
  };

  const fetchSavedScripts = async () => {
    try {
      const response = await fetch('/api/v1/sandbox/scripts');
      const data = await response.json();
      setSavedScripts(data.items || []);
    } catch (error) {
      console.error('Failed to fetch scripts:', error);
    }
  };

  const runCode = async () => {
    setIsRunning(true);
    setOutput('Running...\n');

    try {
      const response = await fetch('/api/v1/sandbox/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language }),
      });

      const data = await response.json();

      if (data.success) {
        setOutput(data.output || 'Execution completed successfully');
      } else {
        setOutput(`Error: ${data.error || 'Unknown error occurred'}`);
      }
    } catch (error) {
      setOutput(`Error: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const saveScript = async () => {
    const name = prompt('Enter script name:');
    if (!name) return;

    try {
      await fetch('/api/v1/sandbox/scripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, code, language }),
      });
      fetchSavedScripts();
      alert('Script saved successfully!');
    } catch (error) {
      alert('Failed to save script');
    }
  };

  const loadScript = (script) => {
    setCode(script.code);
    setLanguage(script.language);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Code Sandbox</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Test and experiment with code in a safe environment
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={saveScript}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Save className="w-5 h-5" />
            Save Script
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <Upload className="w-5 h-5" />
            Import
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Saved Scripts Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Saved Scripts
            </h2>
            <div className="space-y-2">
              {savedScripts.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                  No saved scripts
                </p>
              ) : (
                savedScripts.map((script) => (
                  <div
                    key={script.id}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 cursor-pointer transition-colors"
                    onClick={() => loadScript(script)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {script.name}
                      </span>
                      <FileCode className="w-4 h-4 text-gray-400" />
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {script.language}
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Quick Templates */}
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Quick Templates
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => setLanguage('python')}
                  className="w-full text-left px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Python IFC Parser
                </button>
                <button
                  onClick={() => setLanguage('javascript')}
                  className="w-full text-left px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  JavaScript Cost Calc
                </button>
                <button
                  onClick={() => setLanguage('sql')}
                  className="w-full text-left px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  SQL Query Builder
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Code Editor and Output */}
        <div className="lg:col-span-3 space-y-6">
          {/* Editor Controls */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="sql">SQL</option>
                    <option value="bash">Bash</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setCode('')}
                  className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear
                </button>
                <button
                  onClick={() => navigator.clipboard.writeText(code)}
                  className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  Copy
                </button>
                <button
                  onClick={runCode}
                  disabled={isRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="w-4 h-4" />
                  {isRunning ? 'Running...' : 'Run Code'}
                </button>
              </div>
            </div>

            {/* Code Editor */}
            <div className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full h-96 p-4 font-mono text-sm bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none resize-none"
                placeholder="Write your code here..."
                spellCheck="false"
              />
            </div>
          </div>

          {/* Output Console */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Output Console
                </h2>
              </div>
              <button
                onClick={() => setOutput('')}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                Clear Output
              </button>
            </div>

            <div className="bg-gray-900 rounded-lg p-4 min-h-64 max-h-96 overflow-auto">
              <pre className="font-mono text-sm text-green-400 whitespace-pre-wrap">
                {output || '> Ready to execute code...'}
              </pre>
            </div>
          </div>

          {/* Tips */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
              💡 Sandbox Tips
            </h3>
            <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-1">
              <li>• Use the sandbox to test IFC parsing logic before production</li>
              <li>• All code runs in a secure, isolated environment</li>
              <li>• Access to project data is read-only for safety</li>
              <li>• Save frequently used scripts for quick access</li>
              <li>• Maximum execution time: 30 seconds</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sandbox;
