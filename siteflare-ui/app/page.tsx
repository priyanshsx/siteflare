"use client";

import React, { useState } from 'react';

// 1. Interfaces for SiteFlare and LocalScore
interface SiteFlareScorecard {
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

interface LocalScorecard {
  total_score: number;
  category_scores: {
    average_rating: number;
    total_reviews: number;
    profile_completeness: number;
  };
  recommendations: string[];
  maps_link?: string;
}

export default function MarketingToolsDashboard() {
  const [activeTab, setActiveTab] = useState<'siteflare' | 'localscore'>('siteflare');
  
  // SiteFlare state
  const [url, setUrl] = useState("");
  const [siteLoading, setSiteLoading] = useState(false);
  const [siteError, setSiteError] = useState<string | null>(null);
  const [siteScorecard, setSiteScorecard] = useState<SiteFlareScorecard | null>(null);

  // LocalScore state
  const [localQuery, setLocalQuery] = useState("");
  const [localLoading, setLocalLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [localRequireSignup, setLocalRequireSignup] = useState(false);
  const [localScorecard, setLocalScorecard] = useState<LocalScorecard | null>(null);

  // SiteFlare Audit Call
  const handleSiteAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setSiteLoading(true);
    setSiteError(null);
    setSiteScorecard(null);

    try {
      const response = await fetch("http://localhost:8000/api/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        setSiteError(data.error || "An error occurred while auditing the website.");
      } else {
        setSiteScorecard(data.scorecard);
      }
    } catch (err) {
      setSiteError("Failed to connect to backend. Is FastAPI running?");
    } finally {
      setSiteLoading(false);
    }
  };

  // LocalScore Audit Call
  const handleLocalAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!localQuery) return;

    setLocalLoading(true);
    setLocalError(null);
    setLocalRequireSignup(false);
    setLocalScorecard(null);

    try {
      // Dummy visitor hash for anonymous rate limiting
      const visitorHash = "anon-client-session-1";

      const response = await fetch("http://localhost:8000/api/local", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          query: localQuery,
          visitor_hash: visitorHash
        }),
      });

      const data = await response.json();

      if (data.require_signup) {
        setLocalRequireSignup(true);
        setLocalError(data.error);
      } else if (!response.ok || data.error) {
        setLocalError(data.error || "An error occurred during the local audit.");
      } else {
        setLocalScorecard(data.scorecard);
      }
    } catch (err) {
      setLocalError("Failed to connect to backend. Is FastAPI running?");
    } finally {
      setLocalLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-6">
      
      {/* Navigation Header */}
      <div className="max-w-4xl mx-auto flex justify-center mb-10">
        <div className="bg-slate-200 p-1.5 rounded-full flex gap-2 border border-slate-300">
          <button
            onClick={() => setActiveTab('siteflare')}
            className={`px-6 py-2.5 rounded-full font-bold text-sm transition ${
              activeTab === 'siteflare'
                ? "bg-blue-600 text-white shadow-md"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            SiteFlare (Website Audit)
          </button>
          <button
            onClick={() => setActiveTab('localscore')}
            className={`px-6 py-2.5 rounded-full font-bold text-sm transition ${
              activeTab === 'localscore'
                ? "bg-blue-600 text-white shadow-md"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            LocalScore (GBP Audit)
          </button>
        </div>
      </div>

      {/* TAB 1: SITEFLARE */}
      {activeTab === 'siteflare' && (
        <div>
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h1 className="text-4xl font-black mb-3 text-slate-900">SiteFlare</h1>
            <p className="text-lg text-slate-500 mb-8">Run a deep-dive marketing and AI-readiness audit in seconds.</p>
            
            <form onSubmit={handleSiteAudit} className="flex flex-col sm:flex-row gap-4 justify-center">
              <input 
                type="url" 
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                className="w-full sm:w-96 px-6 py-3.5 rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm text-base"
              />
              <button 
                type="submit" 
                disabled={siteLoading}
                className="px-8 py-3.5 bg-blue-600 text-white font-bold rounded-full hover:bg-blue-700 transition disabled:opacity-50 shadow-md"
              >
                {siteLoading ? "Auditing..." : "Run Website Audit"}
              </button>
            </form>

            {siteError && (
              <div className="mt-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg inline-block text-sm">
                {siteError}
              </div>
            )}
          </div>

          {siteScorecard && (
            <div className="max-w-5xl mx-auto">
              <div className="bg-slate-900 text-white rounded-xl p-8 mb-8 flex items-center justify-between shadow-lg">
                <div>
                  <h2 className="text-2xl font-bold mb-1">Audit Complete</h2>
                  <p className="text-slate-400 text-sm">Target: {url}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <span className="block text-4xl font-black text-blue-400">{siteScorecard.total_score}</span>
                    <span className="text-xs uppercase tracking-widest text-slate-400">Total Score</span>
                  </div>
                  <div className="text-center bg-blue-500/20 border border-blue-500/50 rounded-full h-20 w-20 flex flex-col justify-center items-center">
                    <span className="block text-3xl font-bold text-blue-400">{siteScorecard.letter_grade}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg font-bold text-emerald-800 mb-4">✓ Where You're Good</h3>
                  <ul className="space-y-2.5 text-sm">
                    {siteScorecard.category_scores.ai_readiness >= 15 && (
                      <li className="flex items-start gap-2 text-emerald-900"><span>•</span>AI Crawlers can access and parse content.</li>
                    )}
                    {siteScorecard.category_scores.performance >= 10 && (
                      <li className="flex items-start gap-2 text-emerald-900"><span>•</span>Server load time is optimized.</li>
                    )}
                    {siteScorecard.category_scores.seo >= 15 && (
                      <li className="flex items-start gap-2 text-emerald-900"><span>•</span>On-page SEO setup is solid.</li>
                    )}
                  </ul>
                </div>

                <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 shadow-sm">
                  <h3 className="text-lg font-bold text-rose-800 mb-4">⚠ Action Items</h3>
                  {siteScorecard.recommendations.length > 0 ? (
                    <ul className="space-y-3 text-sm">
                      {siteScorecard.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-rose-900 bg-white p-3 rounded-lg border border-rose-100 shadow-sm">
                          <span className="font-bold text-rose-500">!</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-rose-700 italic text-sm">No critical issues detected.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LOCALSCORE */}
      {activeTab === 'localscore' && (
        <div>
          <div className="max-w-3xl mx-auto text-center mb-12">
            <h1 className="text-4xl font-black mb-3 text-slate-900">LocalScore</h1>
            <p className="text-lg text-slate-500 mb-8">Audit Google Business Profile & Local Search Signals.</p>
            
            <form onSubmit={handleLocalAudit} className="flex flex-col sm:flex-row gap-4 justify-center">
              <input 
                type="text" 
                placeholder="Business name & location (e.g., Joe's Coffee Seattle)"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                required
                className="w-full sm:w-96 px-6 py-3.5 rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm text-base"
              />
              <button 
                type="submit" 
                disabled={localLoading}
                className="px-8 py-3.5 bg-blue-600 text-white font-bold rounded-full hover:bg-blue-700 transition disabled:opacity-50 shadow-md"
              >
                {localLoading ? "Searching..." : "Audit Local Profile"}
              </button>
            </form>

            {localError && (
              <div className="mt-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg inline-block text-sm">
                {localError}
                {localRequireSignup && (
                  <div className="mt-2 font-bold text-blue-600 cursor-pointer underline">
                    Create a free account to continue
                  </div>
                )}
              </div>
            )}
          </div>

          {localScorecard && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-slate-900 text-white rounded-xl p-8 mb-8 flex items-center justify-between shadow-lg">
                <div>
                  <h2 className="text-2xl font-bold mb-1">Local Audit Complete</h2>
                  <p className="text-slate-400 text-sm">Query: {localQuery}</p>
                  {localScorecard.maps_link && (
                    <a 
                      href={localScorecard.maps_link} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="inline-block mt-2 text-xs text-blue-400 underline hover:text-blue-300"
                    >
                      View Google Maps Profile →
                    </a>
                  )}
                </div>
                <div className="text-center">
                  <span className="block text-5xl font-black text-blue-400">{localScorecard.total_score}</span>
                  <span className="text-xs uppercase tracking-widest text-slate-400">Local Score / 100</span>
                </div>
              </div>

              {/* Metric Breakdown Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
                  <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Rating Score</span>
                  <span className="text-3xl font-bold text-slate-800">{localScorecard.category_scores.average_rating} / 40</span>
                </div>
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
                  <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Review Volume</span>
                  <span className="text-3xl font-bold text-slate-800">{localScorecard.category_scores.total_reviews} / 40</span>
                </div>
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
                  <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Profile Setup</span>
                  <span className="text-3xl font-bold text-slate-800">{localScorecard.category_scores.profile_completeness} / 20</span>
                </div>
              </div>

              {/* Recommendations */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-amber-900 mb-3">Recommendations for Google Local Pack</h3>
                {localScorecard.recommendations.length > 0 ? (
                  <ul className="space-y-2 text-sm text-amber-900">
                    {localScorecard.recommendations.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span>•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-amber-800 text-sm">Profile is fully optimized across key local ranking factors!</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
}