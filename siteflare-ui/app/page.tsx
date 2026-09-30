"use client";

import React, { useState } from 'react';

// 1. The TypeScript Interface we defined
interface ScorecardData {
  total_score: number;
  letter_grade: string;
  category_scores: {
    ai_readiness: number;
    performance: number;
    seo: number;
    security_tracking: number;
    [key: string]: number;
  };
  recommendations: string[];
}

export default function SiteFlareHome() {
  // State to handle the user's input and the API response
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scorecard, setScorecard] = useState<ScorecardData | null>(null);

  // 2. The function that talks to your Python backend
  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setScorecard(null);

    try {
      // Calling your FastAPI endpoint
      const response = await fetch("http://localhost:8000/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setError(data.error || "An error occurred while auditing the site.");
      } else {
        setScorecard(data.scorecard);
      }
    } catch (err) {
      setError("Failed to connect to the backend. Is your FastAPI server running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6">
      
      {/* Hero Section & Search Bar */}
      <div className="max-w-3xl mx-auto mt-20 text-center mb-16">
        <h1 className="text-5xl font-black mb-4 text-slate-900">SiteFlare</h1>
        <p className="text-xl text-slate-500 mb-8">Run a deep-dive marketing and AI-readiness audit in seconds.</p>
        
        <form onSubmit={handleAudit} className="flex flex-col sm:flex-row gap-4 justify-center">
          <input 
            type="url" 
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            className="w-full sm:w-96 px-6 py-4 rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm text-lg"
          />
          <button 
            type="submit" 
            disabled={loading}
            className="px-8 py-4 bg-blue-600 text-white font-bold rounded-full hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            {loading ? "Auditing..." : "Run Audit"}
          </button>
        </form>

        {/* Error Message Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg inline-block">
            {error}
          </div>
        )}
      </div>

      {/* The Dashboard Component (Only renders if we have data) */}
      {scorecard && (
        <div className="max-w-6xl mx-auto">
          {/* Top Banner: Score & Grade */}
          <div className="bg-slate-900 text-white rounded-xl p-8 mb-8 flex items-center justify-between shadow-lg">
            <div>
              <h2 className="text-3xl font-bold mb-2">Audit Complete</h2>
              <p className="text-slate-400">Here is how AI agents and search engines see {url}.</p>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <span className="block text-5xl font-black text-blue-400">{scorecard.total_score}</span>
                <span className="text-sm uppercase tracking-widest text-slate-400">Total Score</span>
              </div>
              <div className="text-center bg-blue-500/20 border border-blue-500/50 rounded-full h-24 w-24 flex flex-col justify-center items-center">
                <span className="block text-4xl font-bold text-blue-400">{scorecard.letter_grade}</span>
              </div>
            </div>
          </div>

          {/* Split Layout: Good vs. Bad */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* Where You're Good */}
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-emerald-800 mb-4 flex items-center gap-2">
                <span className="text-2xl">✓</span> Where You're Good
              </h2>
              <ul className="space-y-3">
                {scorecard.category_scores.ai_readiness >= 20 && (
                  <li className="flex items-start gap-3 text-emerald-900"><span className="text-emerald-500">•</span>AI Crawlers can access and parse your content.</li>
                )}
                {scorecard.category_scores.performance >= 10 && (
                  <li className="flex items-start gap-3 text-emerald-900"><span className="text-emerald-500">•</span>Server load time is optimized.</li>
                )}
                {scorecard.category_scores.seo >= 20 && (
                  <li className="flex items-start gap-3 text-emerald-900"><span className="text-emerald-500">•</span>On-page SEO fundamentals are solid.</li>
                )}
              </ul>
            </div>

            {/* Where You're Bad (Action Items) */}
            <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 shadow-sm">
              <h2 className="text-xl font-bold text-rose-800 mb-4 flex items-center gap-2">
                <span className="text-2xl">⚠</span> Critical Action Items
              </h2>
              {scorecard.recommendations.length > 0 ? (
                <ul className="space-y-4">
                  {scorecard.recommendations.map((rec, index) => (
                    <li key={index} className="flex items-start gap-3 text-rose-900 bg-white p-3 rounded-lg border border-rose-100 shadow-sm">
                      <span className="font-bold text-rose-500">!</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-rose-700 italic">No critical issues found. Great job!</p>
              )}
            </div>
          </div>
        </div>
      )}
      
    </div>
  );
}