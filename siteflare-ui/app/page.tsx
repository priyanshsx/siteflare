"use client";

import { useState } from "react";

const categoryDescriptions: Record<string, string> = {
  average_rating: "Measures overall customer satisfaction from your Google reviews.",
  total_reviews: "Evaluates the volume of reviews to indicate business velocity.",
  profile_completeness: "Checks if core business categories and details are filled out.",
  ai_readiness: "Evaluates how easily AI bots can crawl and index your content.",
  seo: "Checks that ensure your page follows basic search engine advice.",
  performance: "Audits that impact the loading speed of your site.",
  content_social: "Analyzes social tags and brand authority indicators.",
  accessibility: "Opportunities to improve accessibility for all visitors.",
  security_tracking: "Ensures standard tracking pixels and secure headers are present."
};

const categoryMaxPoints: Record<string, number> = {
  average_rating: 40,
  total_reviews: 40,
  profile_completeness: 20,
  ai_readiness: 15,
  seo: 22,
  performance: 15,
  content_social: 15,
  accessibility: 10,
  security_tracking: 3
};

const getScoreColor = (percentage: number) => {
  if (percentage >= 90) return "text-emerald-500";
  if (percentage >= 50) return "text-amber-500"; 
  return "text-red-500";
};

const CircularScore = ({ score, maxScore }: { score: number, maxScore: number }) => {
  const percentage = Math.min((score / maxScore) * 100, 100);
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const colorClass = getScoreColor(percentage);

  return (
    <div className="relative inline-flex items-center justify-center w-16 h-16 shrink-0">
      <svg className="w-16 h-16 transform -rotate-90">
        <circle className="text-gray-100" strokeWidth="4" stroke="currentColor" fill="transparent" r={radius} cx="32" cy="32" />
        <circle 
          className={`transition-all duration-1000 ${colorClass}`} 
          strokeWidth="4" 
          strokeDasharray={circumference} 
          strokeDashoffset={offset} 
          strokeLinecap="round" 
          stroke="currentColor" 
          fill="transparent" 
          r={radius} 
          cx="32" 
          cy="32" 
        />
      </svg>
      <span className="absolute text-lg font-bold text-gray-800">{score}</span>
    </div>
  );
};

export default function Home() {
  const [activeTab, setActiveTab] = useState<"website" | "local">("website");
  const [url, setUrl] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
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
      const endpoint = activeTab === "website" ? "/api/audit" : "/api/local";
      const payload = activeTab === "website" ? { url } : { query: searchQuery };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("Failed to fetch audit data");
      
      const data = await response.json();
      if (data.error) {
        if (data.require_signup) {
            throw new Error(data.error);
        }
        throw new Error(data.error);
      }

      setReport(data.scorecard);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans">
      {/* Update font-sans to font-gilroy in your tailwind config if you load the custom font */}
      <div className="max-w-5xl mx-auto space-y-10">
        
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight text-indigo-900" style={{ fontFamily: 'Gilroy, sans-serif' }}>ShopScore</h1>
          <p className="text-lg text-gray-600">The unified digital storefront and local visibility auditor.</p>
        </div>

        <div className="max-w-2xl mx-auto bg-white p-2 rounded-xl shadow-sm border border-gray-100 flex gap-2">
          <button 
            onClick={() => { setActiveTab("website"); setReport(null); setError(""); }}
            className={`flex-1 py-3 rounded-lg font-bold transition-colors ${activeTab === "website" ? "bg-indigo-50 text-indigo-700" : "text-gray-500 hover:bg-gray-50"}`}
          >
            SiteFlare Audit
          </button>
          <button 
            onClick={() => { setActiveTab("local"); setReport(null); setError(""); }}
            className={`flex-1 py-3 rounded-lg font-bold transition-colors ${activeTab === "local" ? "bg-indigo-50 text-indigo-700" : "text-gray-500 hover:bg-gray-50"}`}
          >
            LocalScore Audit
          </button>
        </div>

        <form onSubmit={runAudit} className="flex flex-col gap-4 max-w-2xl mx-auto">
          <div className="flex flex-col md:flex-row gap-4">
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
              <input
                type="text"
                required
                placeholder="e.g., Cafe Pink Hauz Khas Village"
                className="flex-1 px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg font-bold text-lg transition-colors disabled:bg-indigo-400 whitespace-nowrap"
            >
              {loading ? "Auditing..." : "Run Audit"}
            </button>
          </div>
          
          {activeTab === "local" && (
            <div className="bg-blue-50 border border-blue-100 text-blue-800 text-sm p-4 rounded-lg">
              <strong>How to search:</strong>
              <ol className="list-decimal ml-5 mt-1 space-y-1">
                <li>Head to Google Maps.</li>
                <li>Copy the business name exactly as it shows up in English.</li>
                <li>Paste it into the box above along with the city.</li>
              </ol>
            </div>
          )}
        </form>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-center max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {report && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-3">
                <h2 className="text-3xl font-bold">Audit Complete</h2>
                <p className="text-gray-500">Here is how this asset stacks up against modern marketing standards.</p>
                {report.maps_link && (
                  <a 
                    href={report.maps_link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full hover:bg-emerald-100 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    Verified Google Profile
                  </a>
                )}
              </div>
              <div className="flex flex-col items-start md:items-end justify-center">
                <div className="flex items-baseline gap-2">
                  <span className={`text-6xl font-black ${getScoreColor(report.total_score)}`}>{report.total_score}</span>
                  <span className="text-3xl font-bold text-gray-300">/ 100</span>
                </div>
                <span className="text-sm font-bold text-gray-400 uppercase tracking-widest mt-1">Overall Score</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(report.category_scores).map(([key, score]: any) => {
                const displayLabel = key.replace(/_/g, " ");
                const description = categoryDescriptions[key] || "Metric evaluated by our auditing engine.";
                const maxScore = categoryMaxPoints[key] || 100;
                
                return (
                  <div key={key} className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex items-center gap-5 hover:shadow-md transition-shadow">
                    <CircularScore score={score} maxScore={maxScore} />
                    <div className="flex flex-col">
                      <h4 className="text-lg font-bold text-gray-900 capitalize tracking-tight">
                        {displayLabel}
                      </h4>
                      <p className="text-sm text-gray-500 leading-snug mt-0.5">
                        {description}
                      </p>
                    </div>
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