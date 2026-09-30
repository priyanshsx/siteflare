import React from 'react';

export default function SiteFlareDashboard({ scorecard }) {
  if (!scorecard) return null;

  const { total_score, letter_grade, category_scores, recommendations } = scorecard;

  // Derive "Where you're good" by checking which categories scored highly
  // Using arbitrary thresholds for demonstration (e.g., scoring mostly full points)
  const strengths = [];
  if (category_scores.ai_readiness >= 20) strengths.push("AI Crawlers can access and parse your content efficiently.");
  if (category_scores.performance >= 10) strengths.push("Server load time is optimized for quick indexing.");
  if (category_scores.seo >= 20) strengths.push("On-page SEO fundamentals are well-structured.");
  if (category_scores.security_tracking >= 2) strengths.push("Basic security and marketing tracking are active.");

  return (
    <div className="max-w-6xl mx-auto p-6 font-sans">
      
      {/* Top Banner: Score & Grade */}
      <div className="bg-slate-900 text-white rounded-xl p-8 mb-8 flex items-center justify-between shadow-lg">
        <div>
          <h1 className="text-3xl font-bold mb-2">Audit Complete</h1>
          <p className="text-slate-400">Here is how AI agents and search engines see your site.</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <span className="block text-5xl font-black text-blue-400">{total_score}</span>
            <span className="text-sm uppercase tracking-widest text-slate-400">Total Score</span>
          </div>
          <div className="text-center bg-blue-500/20 border border-blue-500/50 rounded-full h-24 w-24 flex flex-col justify-center items-center">
            <span className="block text-4xl font-bold text-blue-400">{letter_grade}</span>
          </div>
        </div>
      </div>

      {/* Split Layout: Good vs. Bad */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Where You're Good */}
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-emerald-800 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
            Where You're Good
          </h2>
          {strengths.length > 0 ? (
            <ul className="space-y-3">
              {strengths.map((strength, index) => (
                <li key={index} className="flex items-start gap-3 text-emerald-900">
                  <span className="text-emerald-500 mt-1">•</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-emerald-700 italic">No major strengths detected in the current audit.</p>
          )}
        </div>

        {/* Where You're Bad (Action Items) */}
        <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 shadow-sm">
          <h2 className="text-xl font-bold text-rose-800 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            Critical Action Items
          </h2>
          {recommendations.length > 0 ? (
            <ul className="space-y-4">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start gap-3 text-rose-900 bg-white p-3 rounded-lg border border-rose-100 shadow-sm">
                  <span className="font-bold text-rose-500">!</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-rose-700 italic">No critical issues found. Your site is well-optimized.</p>
          )}
        </div>
      </div>
      
    </div>
  );
}