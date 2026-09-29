"use client";

import { useState } from "react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"website" | "local">("website");
  
  // Input States
  const [url, setUrl] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [location, setLocation] = useState("");

  // UI States
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState("");

  const runAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      
      // Route the request based on the active tab
      const endpoint = activeTab === "website" ? "/api/audit" : "/api/local";
      const payload = activeTab === "website" 
        ? { url } 
        : { business_name: businessName, location };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("Failed to fetch audit data");
      
      const data = await response.json();
      if (data.error) throw new Error(data.error);

      // Reusing the same scorecard UI for both tools
      setReport(data.scorecard);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-10">
        
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight text-indigo-900">ShopScore</h1>
          <p className="text-lg text-gray-600">The unified digital storefront and local visibility auditor.</p>
        </div>

        <div className="max-w-2xl mx-auto bg-white p-2 rounded-xl shadow-sm border border-gray-100 flex gap-2">
          <button 
            onClick={() => { setActiveTab("website"); setReport(null); setError(""); }}
            className={`flex-1 py-3 rounded-lg font-bold transition-colors ${activeTab === "website" ? "bg-indigo-50 text-indigo-700" : "text-gray-500 hover:bg-gray-50"}`}
          >
            Website Audit
          </button>
          <button 
            onClick={() => { setActiveTab("local"); setReport(null); setError(""); }}
            className={`flex-1 py-3 rounded-lg font-bold transition-colors ${activeTab === "local" ? "bg-indigo-50 text-indigo-700" : "text-gray-500 hover:bg-gray-50"}`}
          >
            Local SEO Audit
          </button>
        </div>

        <form onSubmit={runAudit} className="flex flex-col md:flex-row gap-4 max-w-2xl mx-auto">
          {activeTab === "website" ? (
            <input
              type="url"
              required
              placeholder="https://www.example.com"
              className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          ) : (
            <>
              <input
                type="text"
                required
                placeholder="Business Name (e.g., Joe's Plumbing)"
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
              />
              <input
                type="text"
                required
                placeholder="City, State"
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg font-bold text-lg transition-colors disabled:bg-indigo-400 whitespace-nowrap"
          >
            {loading ? "Auditing..." : "Run Audit"}
          </button>
        </form>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-center max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {report && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold">Audit Complete</h2>
                <p className="text-gray-500">Here is how this asset stacks up against modern marketing standards.</p>
              </div>
              <div className="flex flex-col items-end justify-center">
                <div className="flex items-baseline gap-2">
                  <span className="text-6xl font-black text-indigo-600">{report.total_score}</span>
                  <span className="text-3xl font-bold text-gray-300">/ 100</span>
                </div>
                <span className="text-sm font-bold text-gray-400 uppercase tracking-widest mt-1">Overall Score</span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(report.category_scores).map(([key, score]: any) => {
                let displayLabel = key.replace(/_/g, " ");
                return (
                  <div key={key} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <p className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-2">
                      {displayLabel}
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {score} <span className="text-lg text-gray-400 font-normal">pts</span>
                    </p>
                  </div>
                );
              })}
            </div>

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