"use client";

import { useState, useEffect } from "react";

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
  
  // Auth State
  const [token, setToken] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<"register" | "login">("register");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    const savedToken = localStorage.getItem("shopscore_token");
    if (savedToken) setToken(savedToken);
  }, []);

  const generateVisitorHash = async () => {
    const components = [
      navigator.userAgent,
      window.screen.width,
      window.screen.height,
      navigator.language,
    ].join("|");
    
    const msgBuffer = new TextEncoder().encode(components);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const endpoint = authMode === "register" ? "/api/register" : "/api/login";

    try {
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Authentication failed");

      localStorage.setItem("shopscore_token", data.access_token);
      setToken(data.access_token);
      setShowAuthModal(false);
      setAuthEmail("");
      setAuthPassword("");
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  const logout = () => {
    localStorage.removeItem("shopscore_token");
    setToken(null);
  };

  const runAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setReport(null);

    try {
      const visitorHash = await generateVisitorHash();
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const endpoint = activeTab === "website" ? "/api/audit" : "/api/local";
      
      const payload = activeTab === "website" 
        ? { url, visitor_hash: visitorHash } 
        : { query: searchQuery, visitor_hash: visitorHash };

      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || "Failed to fetch audit data.");
      }
      
      if (data.error) {
        if (data.require_signup) {
            setShowAuthModal(true);
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
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8 font-sans relative">
      
      {/* Top Bar for Auth Status */}
      <div className="absolute top-4 right-8">
        {token ? (
          <button onClick={logout} className="text-sm font-semibold text-gray-500 hover:text-gray-700">
            Sign Out
          </button>
        ) : (
          <button onClick={() => { setAuthMode("login"); setShowAuthModal(true); }} className="text-sm font-semibold text-indigo-600 hover:text-indigo-800">
            Sign In
          </button>
        )}
      </div>

      <div className="max-w-5xl mx-auto space-y-10 mt-8">
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
        </form>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded text-center max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {report && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
             {/* Report UI remains identical */}
             <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-3">
                <h2 className="text-3xl font-bold">Audit Complete</h2>
                <p className="text-gray-500">Here is how this asset stacks up against modern marketing standards.</p>
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
          </div>
        )}
      </div>

      {/* Authentication Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-xl relative animate-in zoom-in-95 duration-200">
            <button 
              onClick={() => setShowAuthModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {authMode === "register" ? "Unlock 5 More Free Audits" : "Welcome Back"}
            </h2>
            <p className="text-gray-500 mb-6">
              {authMode === "register" 
                ? "You've hit your anonymous scan limit. Create a free account to continue auditing."
                : "Sign in to access your remaining audits."}
            </p>
            
            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Email</label>
                <input 
                  type="email" 
                  required 
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-1">Password</label>
                <input 
                  type="password" 
                  required 
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>
              {authError && <p className="text-red-500 text-sm font-semibold">{authError}</p>}
              <button 
                type="submit" 
                className="w-full bg-indigo-600 text-white font-bold py-3 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                {authMode === "register" ? "Create Free Account" : "Sign In"}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-gray-500">
              {authMode === "register" ? "Already have an account? " : "Don't have an account? "}
              <button 
                onClick={() => setAuthMode(authMode === "register" ? "login" : "register")}
                className="font-bold text-indigo-600 hover:text-indigo-800"
              >
                {authMode === "register" ? "Log in here." : "Sign up here."}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}