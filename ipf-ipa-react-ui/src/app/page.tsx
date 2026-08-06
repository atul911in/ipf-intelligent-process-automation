"use client";
import Link from "next/link";

export default function Home() {
  const portals = [
    { href:"/admin", role:"Back Office", title:"Admin Portal", sub:"Document Upload",
      desc:"Upload loan applications and supporting documents for AI-powered processing.", icon:"M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" },
    { href:"/reviewer", role:"Reviewer", title:"Reviewer Portal", sub:"Document Review",
      desc:"Verify OCR extractions, check cross-reference discrepancies and confirm documents.", icon:"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" },
    { href:"/assessor", role:"Credit Assessor", title:"Assessor Portal", sub:"Credit Decision",
      desc:"5-stage NBFI decisioning engine. Review credit scores, risk flags and make loan decisions.", icon:"M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  ];
  return (
    <div className="min-h-screen" style={{background:"linear-gradient(160deg,#00544E 0%,#006E66 50%,#003D39 100%)"}}>
      <header className="px-8 py-5 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center font-black text-lg" style={{background:"#7DC242",color:"#00544E"}}>IPF</div>
          <div>
            <p className="font-bold text-white leading-tight">International Personal Finance</p>
            <p className="text-xs" style={{color:"#7DC242"}}>Intelligent Process Automation Platform</p>
          </div>
        </div>
        <div className="flex gap-2">
          <span className="text-xs text-white/60 bg-white/10 px-3 py-1 rounded-full">PoC v1.0</span>
          <span className="text-xs text-white/60 bg-white/10 px-3 py-1 rounded-full">PL RO HU CZ</span>
        </div>
      </header>
      <div className="text-center px-8 pt-16 pb-10">
        <div className="inline-block text-xs font-bold px-4 py-1.5 rounded-full mb-6 uppercase tracking-widest" style={{background:"#7DC242",color:"#00544E"}}>AI-Powered Demo Platform</div>
        <h1 className="text-5xl font-bold text-white mb-3">IPF Home Credit</h1>
        <p className="text-xl font-light mb-2" style={{color:"#7DC242"}}>Intelligent Loan Origination</p>
        <p className="text-sm text-green-200 max-w-lg mx-auto">End-to-end AI document processing, 5-stage NBFI decisioning engine and credit assessment</p>
      </div>
      <div className="max-w-5xl mx-auto px-8 pb-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        {portals.map((p) => (
          <Link href={p.href} key={p.href} className="group block">
            <div className="bg-white rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
              <div className="p-6" style={{background:"linear-gradient(135deg,#00544E,#006E66)"}}>
                <div className="w-11 h-11 rounded-xl bg-white/20 flex items-center justify-center mb-3">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={p.icon}/>
                  </svg>
                </div>
                <span className="text-xs font-semibold text-white/70 uppercase tracking-wider">{p.role}</span>
                <h2 className="text-xl font-bold text-white mt-0.5">{p.title}</h2>
              </div>
              <div className="p-5">
                <p className="text-sm text-gray-500 leading-relaxed mb-4">{p.desc}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold px-3 py-1 rounded-full" style={{background:"#E8F5E9",color:"#00544E"}}>{p.sub}</span>
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" style={{color:"#7DC242"}} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className="text-center pb-10">
        <p className="text-green-300 text-xs mb-3">Powered by</p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          {["LangGraph","5 AI Agents","FastAPI","SQLite","Next.js","OCR Pipeline"].map(t=>(
            <span key={t} className="text-xs text-green-200 bg-white/10 px-3 py-1 rounded-full">{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
