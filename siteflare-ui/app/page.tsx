"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState("");

  const runAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);

    try {
      // This will call our Python backend once we set up FastAPI
      const response = await fetch("http://127.0.0.1:8000/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) throw new Error("Failed to fetch audit data");
      
      const data = await response.json();
      if (data.error) throw new Error(data.error);

      setReport(data.scorecard);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight text-blue-900">SiteFlare</h1>
          <p className="text-lg text-gray-600">The ultimate technical marketing and AI-readiness audit.</p>
        </div>

        {/* Search Bar */}
        <form onSubmit={runAudit} className="flex gap-4 max-w-2xl mx-auto">
          <input
            type="url"
            required
            placeholder="https://www.example.com"
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-bold text-lg transition-colors disabled:bg-blue-400"
          >
            {loading ? "Auditing..." : "Run Audit"}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-center">
            {error}
          </div>
        )}

        {/* Scorecard Results Dashboard */}
        {report && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            
            {/* Master Score Card */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold">Audit Complete</h2>
                <p className="text-gray-500">Here is how {url} stacks up against modern marketing standards.</p>
              </div>
              <div className="flex flex-col items-end justify-center">
                <div className="flex items-baseline gap-2">
                  <span className="text-6xl font-black text-blue-600">{report.total_score}</span>
                  <span className="text-3xl font-bold text-gray-300">/ 100</span>
                </div>
                <span className="text-sm font-bold text-gray-400 uppercase tracking-widest mt-1">Overall Score</span>
              </div>
            </div>

            {/* Category Breakdown Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(report.category_scores).map(([key, score]: any) => {
                // Map each category to its max points based on your backend rubric
                const maxScores: { [key: string]: number } = {
                  ai_readiness: 30,
                  seo: 25,
                  performance: 15,
                  content_social: 15,
                  accessibility: 10,
                  security_tracking: 5,
                };
                
                const maxScore = maxScores[key];

                // Format the dictionary keys for the UI labels
                let displayLabel = key.replace("_", " ");
                if (key === "content_social") displayLabel = "CONTENT/SOCIAL";
                if (key === "security_tracking") displayLabel = "SECURITY/TRACKING";

                return (
                  <div key={key} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-2">
                      {displayLabel}
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {score} <span className="text-lg text-gray-400 font-normal">/ {maxScore} pts</span>
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Recommendations List */}
            {report.recommendations.length > 0 && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-4">
                <h3 className="text-xl font-bold text-gray-900">Action Items</h3>
                <ul className="space-y-3">
                  {report.recommendations.map((rec: string, idx: number) => (
                    <li key={idx} className="flex gap-3 text-gray-700 bg-red-50 p-4 rounded-lg border border-red-100">
                      <span className="text-red-500 font-bold">→</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}