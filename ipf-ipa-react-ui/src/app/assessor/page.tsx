"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import Link from "next/link";

interface StageCheck {
  rule: string; detail: string; result: string; critical?: boolean;
  bik_score?: number; bik_band?: string; product_route?: string; max_loan_amount?: number;
  big_debt_amount?: number; dti_ratio?: number; dti_cap?: number;
  verified_income?: number; legal_max_cost?: number;
}
interface StageResult {
  stage: string; description: string; checks: StageCheck[];
  passed: boolean; rejection_reason?: string;
  bik_score?: number; big_debt?: number; affordability_flags?: string[];
}
interface CreditScore {
  score: number; score_pct: number; risk_band: string; risk_icon: string;
  recommendation: string; product_route?: string; max_approved_amount?: number;
  decision_reason?: string; bureau_name: string; disclaimer: string;
  breakdown: Array<{category:string;score:number;max:number;pct:number;detail:string}>;
  flags: string[]; bik_score?: number; bik_band?: string;
  big_debt?: number; dti_ratio?: number; dti_cap?: number; verified_income?: number;
  stage_results?: StageResult[];
}
interface DocItem { id: string; filename: string; original_filename?: string; type: string; status: string; }
interface Discrepancy { id:string; label:string; status:string; severity:string; declared_value:string; extracted_value:string; detail:string; }

function Spinner() {
  return (
    <svg className="animate-spin w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
  );
}


// =================== 5-STAGE DECISIONING DISPLAY ===================
function DecisioningStagesDisplay({ stageResults }: { stageResults: StageResult[] }) {
  const [expandedStage, setExpandedStage] = useState<string|null>(null);
  if (!stageResults || stageResults.length === 0) return null;

  const STAGE_COLORS: Record<string, string> = {
    'Stage 0: Regulatory Gateway': '#6366f1',
    'Stage 1: Fraud & Identity Engine': '#8b5cf6',
    'Stage 2: Bureau Routing (BIK + BIG)': '#0284c7',
    'Stage 3: Legal Caps & Affordability': '#0891b2',
    'Stage 4: Final Decision Matrix': '#059669',
  };

  return (
    <div className='mt-6'>
      <h3 className='font-bold text-gray-900 mb-1'>5-Stage NBFI Decisioning Engine</h3>
      <p className='text-xs text-gray-500 mb-4'>Polish home credit model (Provident Polska / IPF aligned). Click any stage to see rule-by-rule breakdown.</p>
      <div className='space-y-3'>
        {stageResults.map((stage, i) => {
          const color = STAGE_COLORS[stage.stage] || '#6b7280';
          const isOpen = expandedStage === stage.stage;
          const hasReject = !stage.passed;
          return (
            <div key={i} className={'border-2 rounded-xl overflow-hidden '+(hasReject?'border-red-300':stage.passed?'border-green-200':'border-gray-200')}>
              <button onClick={()=>setExpandedStage(isOpen?null:stage.stage)}
                className={'w-full flex items-center justify-between px-4 py-3 text-left hover:opacity-90 transition-opacity'}
                style={{background: color+'15',borderLeft:'3px solid '+color}}>
                <div className='flex items-center gap-3'>
                  <div className='w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0'
                    style={{backgroundColor: hasReject?'#ef4444':color}}>
                    {hasReject ? 'X' : (i+1)}
                  </div>
                  <div className='text-left'>
                    <p className='font-semibold text-gray-900 text-sm'>{stage.stage}</p>
                    <p className='text-xs text-gray-500'>{stage.description}</p>
                  </div>
                </div>
                <div className='flex items-center gap-2 flex-shrink-0'>
                  {stage.bik_score !== undefined && (
                    <span className='text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full'>BIK: {stage.bik_score}/100</span>
                  )}
                  {stage.big_debt !== undefined && stage.big_debt > 0 && (
                    <span className='text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full'>{stage.big_debt} PLN debt</span>
                  )}
                  <span className={'text-xs font-bold px-3 py-1 rounded-full '+(hasReject?'bg-red-100 text-red-700':'bg-green-100 text-green-700')}>
                    {hasReject ? 'BLOCKED' : 'PASSED'}
                  </span>
                  <svg className={'w-4 h-4 text-gray-400 transition-transform '+(isOpen?'rotate-180':'')} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7'/>
                  </svg>
                </div>
              </button>
              {isOpen && (
                <div className='border-t border-gray-200 bg-white p-4 space-y-3'>
                  {stage.rejection_reason && (
                    <div className='bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 font-medium'>
                      Rejection reason: {stage.rejection_reason}
                    </div>
                  )}
                  {stage.affordability_flags && stage.affordability_flags.length > 0 && (
                    <div className='bg-amber-50 border border-amber-200 rounded-lg p-3'>
                      <p className='text-xs font-semibold text-amber-800 mb-1'>Affordability Flags:</p>
                      {stage.affordability_flags.map((f,j)=><p key={j} className='text-xs text-amber-700'>- {f}</p>)}
                    </div>
                  )}
                  {stage.checks.map((chk, j) => (
                    <div key={j} className={'border rounded-lg p-3 '+(chk.result==='REJECT'?'bg-red-50 border-red-200':chk.result==='WARN'?'bg-amber-50 border-amber-200':chk.result==='PASS'||chk.result==='APPROVE'?'bg-green-50 border-green-200':'bg-blue-50 border-blue-200')}>
                      <div className='flex items-start justify-between gap-3'>
                        <div className='flex-1'>
                          <p className='text-xs font-bold text-gray-800 mb-1'>{chk.rule}</p>
                          <p className='text-xs text-gray-600 leading-relaxed'>{chk.detail}</p>
                        </div>
                        <span className={'text-xs font-bold px-2 py-1 rounded-full flex-shrink-0 '+(chk.result==='REJECT'?'bg-red-200 text-red-800':chk.result==='WARN'?'bg-amber-200 text-amber-800':'bg-green-200 text-green-800')}>
                          {chk.result}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
function ScoreGauge({ score, maxScore=1000 }: { score: number; maxScore?: number }) {
  const pct = Math.min(100, (score / maxScore) * 100);
  const color = pct >= 65 ? "#10b981" : pct >= 40 ? "#f59e0b" : "#ef4444";
  const circumference = 2 * Math.PI * 45;
  const dashOffset = circumference - (pct / 100) * circumference;
  return (
    <div className="flex flex-col items-center">
      <svg width="130" height="130" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r="45" fill="none" stroke="#e5e7eb" strokeWidth="10"/>
        <circle cx="55" cy="55" r="45" fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circumference} strokeDashoffset={dashOffset}
          strokeLinecap="round" transform="rotate(-90 55 55)" style={{transition:"stroke-dashoffset 0.8s ease"}}/>
        <text x="55" y="52" textAnchor="middle" fontSize="18" fontWeight="bold" fill="#111827">{score}</text>
        <text x="55" y="66" textAnchor="middle" fontSize="9" fill="#6b7280">/ {maxScore}</text>
      </svg>
    </div>
  );
}

const FLAG_EXPLANATIONS: Record<string, string> = {
  income: "The declared income on the loan application does not match the figure on the payslip or income certificate. A variance above 10% is a lending policy concern and may indicate misrepresentation.",
  employment: "No employer details could be extracted from the submitted income documents. Employment status and stability are key affordability factors.",
  expired: "The submitted identity document has passed its expiry date and is no longer valid under EU and national identity verification regulations.",
  "national id": "The national identification number failed the built-in checksum or format validation. This may indicate a data entry error or fraudulent document.",
  address: "The residential address declared on the loan application does not match the address on the proof-of-address document.",
  age: "The applicant's age falls outside the eligible lending range (18-70 years). This is a product eligibility requirement.",
  name: "There is an inconsistency between the applicant name on the loan application and the name extracted from the identity document.",
};

function getFlagExplanation(flag: string): string {
  const lower = flag.toLowerCase();
  for (const [key, val] of Object.entries(FLAG_EXPLANATIONS)) {
    if (lower.includes(key)) return val;
  }
  return "This flag requires manual review by the assessor before a final decision is made.";
}

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [pw, setPw] = useState(""); const [err, setErr] = useState("");
  const login = () => {
    if (pw === (process.env.NEXT_PUBLIC_ASSESSOR_PASSWORD || "ipf-assessor-2026")) { onLogin(); }
    else { setErr("Invalid password."); }
  };
  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{background:"linear-gradient(160deg,#00544E,#003D39)"}}>
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" style={{background:"#E8F5E9"}}>
            <svg className="w-8 h-8 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg mx-auto mb-2" style={{background:"#00544E",color:"#7DC242"}}>IPF</div><h1 className="text-2xl font-bold text-gray-900">Credit Assessor Portal</h1>
          <p className="text-gray-500 mt-1">IPF Intelligent Process Automation</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Assessor Password</label>
            <input type="password" value={pw} onChange={e=>setPw(e.target.value)}
              onKeyDown={e=>e.key==="Enter"&&login()}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Enter password"/>
          </div>
          {err && <p className="text-red-600 text-sm">{err}</p>}
          <button onClick={login} className="w-full text-white font-semibold py-3 rounded-lg transition-colors" style={{background:"#00544E"}}>Login</button>
          <Link href="/" className="block text-center text-sm text-gray-500 hover:text-gray-700">Back to Portal Selection</Link>
        </div>
      </div>
    </div>
  );
}

// =================== DECISION QUEUE ===================
function DecisionQueueTab({ onSelectApp }: { onSelectApp: (id:string)=>void }) {
  const [items, setItems] = useState<Record<string,DocItem[]>>({});
  const [scores, setScores] = useState<Record<string,CreditScore>>({});
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/api/queue');
      const all: DocItem[] = r.data.items || [];
      const grouped: Record<string,DocItem[]> = {};
      all.forEach(d=>{
        const k = (d as unknown as Record<string,string>).application_id || 'unknown';
        if (!grouped[k]) grouped[k] = [];
        grouped[k].push(d);
      });
      setItems(grouped);
      // Load credit scores for each app
      await Promise.all(Object.keys(grouped).map(async appId => {
        try {
          const cs = await api.get('/api/credit-score/'+appId);
          setScores(prev=>({...prev,[appId]:cs.data}));
        } catch { /* no score yet */ }
      }));
    } catch { setItems({}); }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ load(); }, [load]);

  const getRiskColor = (band: string) => {
    if (!band) return 'text-gray-600';
    if (band.includes('LOW')) return 'text-green-600';
    if (band.includes('HIGH')) return 'text-red-600';
    return 'text-amber-600';
  };

  return (
    <div>
      <div className='flex items-center justify-between mb-4'>
        <h2 className='text-lg font-bold text-gray-900'>Applications Awaiting Decision</h2>
        <button onClick={load} className='text-sm font-medium' style={{color:'#00544E'}}>Refresh</button>
      </div>
      {loading && <div className='flex justify-center py-10'><Spinner/></div>}
      {!loading && Object.keys(items).length === 0 && (
        <div className='text-center py-12 text-gray-400'>No applications in queue. Documents may still be processing.</div>
      )}
      {!loading && Object.entries(items).map(([appId, docs]) => {
        const cs = scores[appId];
        const verified = docs.filter(d=>d.status==='VERIFIED').length;
        const market = (docs[0] as unknown as Record<string,string>)?.market || '';
        return (
          <div key={appId} className='mb-4 border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow'>
            <div className='p-4 flex items-center justify-between'>
              <div className='flex items-center gap-6'>
                <div>
                  <p className='font-bold text-gray-900'>{appId}</p>
                  <p className='text-sm text-gray-500'>{market} market</p>
                </div>
                <div className='text-center'>
                  <p className='text-xs text-gray-500'>Documents</p>
                  <p className='font-semibold text-gray-800'>{verified}/{docs.length} verified</p>
                </div>
                {cs && (
                  <>
                    <div className='text-center'>
                      <p className='text-xs text-gray-500'>Credit Score</p>
                      <p className={'text-xl font-bold '+getRiskColor(cs.risk_band)}>{cs.score}<span className='text-sm font-normal text-gray-400'>/1000</span></p>
                    </div>
                    <div className='text-center'>
                      <p className='text-xs text-gray-500'>Risk Band</p>
                      <p className={'font-semibold text-sm '+getRiskColor(cs.risk_band)}>{cs.risk_band}</p>
                    </div>
                    <div className='text-center'>
                      <p className='text-xs text-gray-500'>AI Says</p>
                      <p className={'font-semibold text-sm '+(cs.recommendation==='APPROVE'?'text-green-600':cs.recommendation==='DECLINE'?'text-red-600':'text-amber-600')}>{cs.recommendation}</p>
                    </div>
                  </>
                )}
              </div>
              <button onClick={()=>onSelectApp(appId)}
                className='text-white font-semibold px-5 py-2 rounded-xl transition-colors' style={{background:'#00544E'}}>
                Review and Decide
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// =================== APPLICATION SUMMARY ===================
function AppSummaryTab({ initialAppId, onProceedToDecision }: { initialAppId: string; onProceedToDecision: (id:string)=>void }) {
  const [inputId, setInputId] = useState(initialAppId);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Record<string,unknown>|null>(null);
  const [loanApp, setLoanApp] = useState<Record<string,unknown>|null>(null);
  const [cs, setCs] = useState<CreditScore|null>(null);
  const [discData, setDiscData] = useState<{summary:Record<string,number>;discrepancies:Discrepancy[]}|null>(null);
  const [expandedFlag, setExpandedFlag] = useState<string|null>(null);
  const [expandBreakdown, setExpandBreakdown] = useState(false);

  const loadApp = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true); setStatus(null); setLoanApp(null); setCs(null); setDiscData(null);
    try {
      const [sr,lr,csr,dr] = await Promise.all([
        api.get('/api/status/'+id).catch(()=>null),
        api.get('/api/loan-application/'+id).catch(()=>null),
        api.get('/api/credit-score/'+id).catch(()=>null),
        api.get('/api/discrepancies/'+id).catch(()=>null),
      ]);
      if (sr) setStatus(sr.data);
      if (lr) setLoanApp(lr.data);
      if (csr) setCs(csr.data);
      if (dr) setDiscData(dr.data);
    } catch { /* per-request */ }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ if (initialAppId) { setInputId(initialAppId); loadApp(initialAppId); } }, [initialAppId, loadApp]);

  const docs = (status?.documents as DocItem[]) || [];
  const verified = docs.filter(d=>d.status==='VERIFIED').length;
  const fields = (loanApp as Record<string,Record<string,{value?:string}|string>>)?.extracted_fields || {};
  const disc = discData?.discrepancies || [];
  const dsum = discData?.summary || {};
  const mismatches = (disc as Discrepancy[]).filter(d=>d.status==='MISMATCH');
  const warnings = (disc as Discrepancy[]).filter(d=>d.status==='WARNING');

  const SHOW: Record<string,string> = {
    applicant_full_name:'Full Name', date_of_birth:'Date of Birth', residential_address:'Address',
    declared_net_monthly_income:'Declared Income', declared_income_currency:'Currency',
    requested_loan_amount:'Loan Requested', loan_term_weeks:'Loan Term (weeks)',
    employment_status:'Employment', employer_name:'Employer', purpose_of_loan:'Purpose',
  };

  return (
    <div>
      <div className='flex gap-3 mb-6'>
        <input type='text' value={inputId} onChange={e=>setInputId(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&(()=>{loadApp(inputId);})()}
          className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-400'
          placeholder='Application ID e.g. APP-PL-GOOD-001'/>
        <button onClick={()=>loadApp(inputId)} className='bg-teal-600 hover:bg-teal-700 text-white font-semibold px-5 py-2 rounded-lg'>Load</button>
      </div>
      {loading && <div className='flex justify-center py-12'><Spinner/></div>}
      {status && (
        <div>
          {/* Top metrics */}
          <div className='grid grid-cols-4 gap-4 mb-6'>
            <div className={'rounded-xl p-4 text-center border '+(verified===docs.length?'bg-green-50 border-green-200':'bg-amber-50 border-amber-200')}>
              <div className={'text-2xl font-bold '+(verified===docs.length?'text-green-700':'text-amber-700')}>{verified}/{docs.length}</div>
              <div className='text-xs font-semibold text-gray-600 mt-0.5'>Documents Verified</div>
            </div>
            <div className={'rounded-xl p-4 text-center border '+(cs?(cs.score>=650?'bg-green-50 border-green-200':cs.score>=400?'bg-amber-50 border-amber-200':'bg-red-50 border-red-200'):'bg-gray-50 border-gray-200')}>
              <div className={'text-2xl font-bold '+(cs?(cs.score>=650?'text-green-700':cs.score>=400?'text-amber-700':'text-red-700'):'text-gray-400')}>{cs?.score||'-'}</div>
              <div className='text-xs font-semibold text-gray-600 mt-0.5'>Credit Score /1000</div>
            </div>
            <div className={'rounded-xl p-4 text-center border bg-gray-50 border-gray-200'}>
              <div className='text-2xl font-bold text-gray-800'>{cs?.risk_band||'-'}</div>
              <div className='text-xs font-semibold text-gray-600 mt-0.5'>Risk Band</div>
            </div>
            <div className={'rounded-xl p-4 text-center border '+((dsum.mismatches||0)>0?'bg-red-50 border-red-200':'bg-green-50 border-green-200')}>
              <div className={'text-2xl font-bold '+((dsum.mismatches||0)>0?'text-red-700':'text-green-700')}>{dsum.mismatches||0}</div>
              <div className='text-xs font-semibold text-gray-600 mt-0.5'>Discrepancies</div>
            </div>
          </div>

          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
            {/* Applicant Details */}
            <div className='bg-white border border-gray-200 rounded-xl p-5'>
              <h3 className='font-bold text-gray-900 mb-4'>Applicant Details</h3>
              {loanApp ? (
                <div className='space-y-2'>
                  {Object.entries(SHOW).map(([key,label])=>{
                    const fd = fields[key];
                    const val = (typeof fd==='object'&&fd!==null&&'value' in fd)?fd.value:(fd as string);
                    if (!val||val==='None') return null;
                    return (
                      <div key={key} className='flex justify-between py-1.5 border-b border-gray-100'>
                        <span className='text-sm text-gray-500 w-40 shrink-0'>{label}</span>
                        <span className='text-sm font-medium text-gray-800 text-right'>{val as string}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className='text-gray-400 text-sm'>No loan application form uploaded</p>
              )}
            </div>

            {/* Credit Assessment */}
            <div className='bg-white border border-gray-200 rounded-xl p-5'>
              <h3 className='font-bold text-gray-900 mb-4'>Credit Assessment</h3>
              {cs ? (
                <div>
                  <div className='flex items-center gap-6 mb-4'>
                    <ScoreGauge score={cs.score}/>
                    <div>
                      <p className='text-3xl font-bold text-gray-900'>{cs.score}<span className='text-base font-normal text-gray-400'>/1000</span></p>
                      <p className={'text-lg font-semibold '+(cs.score>=650?'text-green-600':cs.score>=400?'text-amber-600':'text-red-600')}>{cs.risk_band}</p>
                      <p className={'font-semibold mt-1 '+(cs.recommendation==='APPROVE'?'text-green-600':cs.recommendation==='DECLINE'?'text-red-600':'text-amber-600')}>
                        AI: {cs.recommendation}
                      </p>
                      <p className='text-xs text-gray-400 mt-1'>{cs.bureau_name}</p>
                    </div>
                  </div>
                  {/* Score bar */}
                  <div className='w-full bg-gray-200 rounded-full h-2 mb-4'>
                    <div className={'h-2 rounded-full transition-all duration-700 '+(cs.score>=650?'bg-[#7DC242]':cs.score>=400?'bg-amber-500':'bg-red-500')}
                      style={{width:cs.score_pct+'%'}}/>
                  </div>
                  {/* Score Breakdown */}
                  <button onClick={()=>setExpandBreakdown(!expandBreakdown)} className='text-sm font-medium flex items-center gap-1' style={{color:'#00544E'}}>
                    Score Breakdown
                    <svg className={'w-4 h-4 transition-transform '+(expandBreakdown?'rotate-180':'')} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7'/>
                    </svg>
                  </button>
                  {expandBreakdown && (
                    <div className='mt-2 space-y-2'>
                      {cs.breakdown.map((b,i)=>(
                        <div key={i}>
                          <div className='flex justify-between text-xs mb-0.5'>
                            <span className='text-gray-600'>{b.category}</span>
                            <span className='text-gray-800 font-medium'>{b.score}/{b.max}</span>
                          </div>
                          <div className='w-full bg-gray-100 rounded h-1.5'>
                            <div className='bg-teal-500 h-1.5 rounded transition-all' style={{width:b.pct+'%'}}/>
                          </div>
                          <p className='text-xs text-gray-400 mt-0.5'>{b.detail}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Risk Flags */}
                  {cs.flags.length > 0 && (
                    <div className='mt-4'>
                      <h4 className='font-semibold text-red-700 text-sm mb-2'>Risk Flags Detected ({cs.flags.length})</h4>
                      <div className='space-y-2'>
                        {cs.flags.map((flag,i)=>(
                          <div key={i} className='border border-red-200 rounded-xl overflow-hidden'>
                            <button onClick={()=>setExpandedFlag(expandedFlag===flag?null:flag)}
                              className='w-full flex items-center justify-between px-3 py-2 bg-red-50 hover:bg-red-100 text-left'>
                              <span className='text-sm font-medium text-red-800'>{flag}</span>
                              <svg className={'w-4 h-4 text-red-500 transition-transform '+(expandedFlag===flag?'rotate-180':'')} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7'/>
                              </svg>
                            </button>
                            {expandedFlag===flag && (
                              <div className='px-3 py-2 bg-white text-xs text-gray-700 border-t border-red-100'>
                                {getFlagExplanation(flag)}
                                <p className='text-gray-400 mt-1'>Source: AI document analysis | This explanation is system-generated to assist the assessor.</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {cs.flags.length===0 && <div className='mt-3 bg-green-50 border border-green-200 rounded-lg p-2 text-xs text-green-700'>No risk flags detected</div>}
                  {/* Decision Info */}
                  {cs.product_route && (
                    <div className='mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg'>
                      <p className='text-xs font-bold text-blue-800 mb-0.5'>Product Route: {cs.product_route}</p>
                      {cs.max_approved_amount ? <p className='text-xs text-blue-700'>Max Approved: {cs.max_approved_amount.toLocaleString()} PLN</p> : null}
                      {cs.decision_reason && <p className='text-xs text-gray-600 mt-1'>{cs.decision_reason}</p>}
                    </div>
                  )}
                  {/* 5-Stage Pipeline */}
                  {cs.stage_results && <DecisioningStagesDisplay stageResults={cs.stage_results}/>}
                </div>
              ) : (
                <p className='text-gray-400 text-sm'>Credit score not yet available. Ensure documents are processed.</p>
              )}
            </div>
          </div>

          {/* Discrepancies Summary */}
          {(mismatches.length>0||warnings.length>0) && (
            <div className='bg-white border border-gray-200 rounded-xl p-5 mb-6'>
              <h3 className='font-bold text-gray-900 mb-3'>Document Discrepancies</h3>
              {mismatches.map((d,i)=>(
                <div key={i} className='bg-red-50 border border-red-200 rounded-lg p-3 mb-2'>
                  <span className='font-semibold text-red-800 text-sm'>{d.label} - MISMATCH</span>
                  <div className='text-xs text-gray-600 mt-1'>Declared: {d.declared_value} | Extracted: {d.extracted_value}</div>
                </div>
              ))}
              {warnings.map((d,i)=>(
                <div key={i} className='bg-amber-50 border border-amber-200 rounded-lg p-3 mb-2'>
                  <span className='font-semibold text-amber-800 text-sm'>{d.label} - WARNING</span>
                  <div className='text-xs text-gray-600 mt-1'>{d.detail}</div>
                </div>
              ))}
            </div>
          )}
          {(mismatches.length===0&&warnings.length===0&&disc.length>0) && (
            <div className='bg-green-50 border border-green-200 rounded-lg p-3 mb-6 text-sm text-green-700'>All checked fields are consistent - no discrepancies.</div>
          )}

          <button onClick={()=>onProceedToDecision(inputId)}
            className='w-full text-white font-bold py-3 rounded-xl transition-colors' style={{background:'#00544E'}}>
            Proceed to Final Decision
          </button>
        </div>
      )}
    </div>
  );
}

// =================== LOAN DECISION TAB ===================
function LoanDecisionTab({ initialAppId }: { initialAppId: string }) {
  const [inputId, setInputId] = useState(initialAppId);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Record<string,unknown>|null>(null);
  const [cs, setCs] = useState<CreditScore|null>(null);
  const [loanApp, setLoanApp] = useState<Record<string,unknown>|null>(null);
  const [discData, setDiscData] = useState<{summary:Record<string,number>}|null>(null);
  const [reasonCodes, setReasonCodes] = useState<string[]>([]);
  const [notes, setNotes] = useState('');
  const [decisionResult, setDecisionResult] = useState<{decision:string;msg:string}|null>(null);
  const [submitting, setSubmitting] = useState(false);

  const REASON_OPTIONS = [
    'Income sufficient','Identity verified','Address verified',
    'Income insufficient','Income discrepancy','Identity concerns',
    'Address mismatch','Expired document','Policy compliance','Other - see notes'
  ];

  const loadApp = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true); setStatus(null); setCs(null); setLoanApp(null); setDiscData(null); setDecisionResult(null);
    try {
      const [sr,csr,lr,dr] = await Promise.all([
        api.get('/api/status/'+id).catch(()=>null),
        api.get('/api/credit-score/'+id).catch(()=>null),
        api.get('/api/loan-application/'+id).catch(()=>null),
        api.get('/api/discrepancies/'+id).catch(()=>null),
      ]);
      if (sr) setStatus(sr.data);
      if (csr) setCs(csr.data);
      if (lr) setLoanApp(lr.data);
      if (dr) setDiscData(dr.data);
    } catch { /* per-req */ }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ if (initialAppId) { setInputId(initialAppId); loadApp(initialAppId); } }, [initialAppId, loadApp]);

  const submitDecision = async (decision: string) => {
    if (decision==='DECLINE'&&!reasonCodes.length&&!notes) { alert('Please provide at least one reason code or note before declining.'); return; }
    setSubmitting(true);
    try {
      const codes = [...reasonCodes, ...(notes?[notes]:[])];
      await api.post('/api/decision/'+inputId, { decision, assessor_id: 'credit_assessor', reason_codes: codes });
      setDecisionResult({ decision, msg: decision==='APPROVE'?'Loan APPROVED and recorded in system.':'Loan DECLINED and recorded in system.' });
    } catch { setDecisionResult({ decision:'ERROR', msg:'Failed to record decision. Please try again.' }); }
    finally { setSubmitting(false); }
  };

  const docs = (status?.documents as DocItem[]) || [];
  const verified = docs.filter(d=>d.status==='VERIFIED').length;
  const mismatches = (discData?.summary?.mismatches||0);
  const rec = (status?.recommendation as string) || cs?.recommendation || '';

  const lf = (loanApp as Record<string,Record<string,{value?:string}|string>>)?.extracted_fields || {};
  const nameField = lf.applicant_full_name;
  const name = (typeof nameField==='object'&&nameField&&'value' in nameField)?nameField.value:(nameField as string);

  return (
    <div>
      <div className='flex gap-3 mb-6'>
        <input type='text' value={inputId} onChange={e=>setInputId(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&loadApp(inputId)}
          className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-teal-400'
          placeholder='Application ID e.g. APP-PL-GOOD-001'/>
        <button onClick={()=>loadApp(inputId)} className='bg-teal-600 hover:bg-teal-700 text-white font-semibold px-5 py-2 rounded-lg'>Load</button>
      </div>
      {loading && <div className='flex justify-center py-12'><Spinner/></div>}

      {decisionResult && (
        <div className={'mb-6 p-5 rounded-xl text-center '+(decisionResult.decision==='APPROVE'?'bg-green-50 border-2 border-green-300':decisionResult.decision==='DECLINE'?'bg-red-50 border-2 border-red-300':'bg-gray-50 border border-gray-200')}>
          <p className={'text-xl font-bold '+(decisionResult.decision==='APPROVE'?'text-green-700':decisionResult.decision==='DECLINE'?'text-red-700':'text-gray-700')}>{decisionResult.msg}</p>
          {decisionResult.decision==='APPROVE'&&<p className='text-green-600 mt-1'>Decision logged and application closed.</p>}
        </div>
      )}

      {status && !decisionResult && (
        <div>
          {/* Status bar */}
          <div className='grid grid-cols-4 gap-4 mb-6'>
            <div className={'p-4 rounded-xl text-center border '+(verified===docs.length&&docs.length>0?'bg-green-50 border-green-200':'bg-amber-50 border-amber-200')}>
              <div className={'text-xl font-bold '+(verified===docs.length?'text-green-700':'text-amber-700')}>{verified}/{docs.length}</div>
              <div className='text-xs text-gray-500 mt-0.5'>Documents</div>
            </div>
            <div className='p-4 rounded-xl text-center border bg-gray-50 border-gray-200'>
              <div className='text-xl font-bold text-gray-800'>{cs?.score||'-'}/1000</div>
              <div className='text-xs text-gray-500 mt-0.5'>Credit Score</div>
            </div>
            <div className={'p-4 rounded-xl text-center border '+(cs?.score?cs.score>=650?'bg-green-50 border-green-200':cs.score>=400?'bg-amber-50 border-amber-200':'bg-red-50 border-red-200':'bg-gray-50 border-gray-200')}>
              <div className={'text-sm font-bold '+(cs?.score?cs.score>=650?'text-green-700':cs.score>=400?'text-amber-700':'text-red-700':'text-gray-400')}>{cs?.risk_band||'-'}</div>
              <div className='text-xs text-gray-500 mt-0.5'>Risk Band</div>
            </div>
            <div className={'p-4 rounded-xl text-center border '+(mismatches>0?'bg-red-50 border-red-200':'bg-green-50 border-green-200')}>
              <div className={'text-xl font-bold '+(mismatches>0?'text-red-700':'text-green-700')}>{mismatches}</div>
              <div className='text-xs text-gray-500 mt-0.5'>Mismatches</div>
            </div>
          </div>

          {name && <div className='mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800'>Applicant: <strong>{name}</strong> | Application: <strong>{inputId}</strong></div>}

          {/* AI Recommendation */}
          {rec && (
            <div className={'mb-6 p-4 rounded-xl border-2 '+(rec==='APPROVE'?'bg-green-50 border-green-300':rec==='DECLINE'?'bg-red-50 border-red-300':'bg-amber-50 border-amber-300')}>
              <p className={'font-bold text-lg '+(rec==='APPROVE'?'text-green-700':rec==='DECLINE'?'text-red-700':'text-amber-700')}>AI Recommendation: {rec}</p>
              <p className='text-xs text-gray-500 mt-1'>This is an AI recommendation only. The final decision is always yours.</p>
            </div>
          )}

          {verified < docs.length && docs.length > 0 && (
            <div className='mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800'>
              Only {verified}/{docs.length} documents verified. It is recommended all documents are reviewed before deciding.
            </div>
          )}

          {/* Reason codes */}
          <div className='bg-white border border-gray-200 rounded-xl p-5 mb-6'>
            <h3 className='font-bold text-gray-900 mb-3'>Reason Codes (select all that apply)</h3>
            <div className='grid grid-cols-2 gap-2'>
              {REASON_OPTIONS.map(r=>(
                <label key={r} className='flex items-center gap-2 cursor-pointer text-sm'>
                  <input type='checkbox' checked={reasonCodes.includes(r)} onChange={e=>{
                    setReasonCodes(prev=>e.target.checked?[...prev,r]:prev.filter(x=>x!==r));
                  }} className='accent-teal-600'/>
                  <span className='text-gray-700'>{r}</span>
                </label>
              ))}
            </div>
            <div className='mt-3'>
              <label className='block text-sm font-medium text-gray-700 mb-1'>Additional Notes</label>
              <textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={2}
                className='w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400'
                placeholder='Optional notes for this decision'/>
            </div>
          </div>

          {/* Decision buttons */}
          <div className='grid grid-cols-2 gap-4'>
            <div className='bg-green-50 border-2 border-green-200 rounded-xl p-5 text-center'>
              <h3 className='font-bold text-green-800 text-lg mb-1'>Approve</h3>
              <p className='text-sm text-green-600 mb-4'>Application meets all lending criteria</p>
              <button onClick={()=>submitDecision('APPROVE')} disabled={submitting}
                className='w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold py-3 rounded-xl transition-colors'>
                {submitting?'Submitting...':'APPROVE LOAN'}
              </button>
            </div>
            <div className='bg-red-50 border-2 border-red-200 rounded-xl p-5 text-center'>
              <h3 className='font-bold text-red-800 text-lg mb-1'>Decline</h3>
              <p className='text-sm text-red-600 mb-4'>Application does not meet lending criteria</p>
              <button onClick={()=>submitDecision('DECLINE')} disabled={submitting}
                className='w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white font-bold py-3 rounded-xl transition-colors'>
                {submitting?'Submitting...':'DECLINE LOAN'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =================== DECISION HISTORY ===================
function DecisionHistoryTab() {
  const [history, setHistory] = useState<Array<Record<string,unknown>>>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.get('/api/upload/history');
      const decided = (r.data.uploads||[]).filter((u:Record<string,string>)=>u.status==='DECIDED');
      // Enrich with credit score
      const enriched = await Promise.all(decided.map(async (u:Record<string,unknown>)=>{
        try {
          const [cs,audit] = await Promise.all([
            api.get('/api/credit-score/'+u.application_id).catch(()=>null),
            api.get('/api/audit/'+u.application_id).catch(()=>null),
          ]);
          const decisions = (audit?.data?.audit_trail||[]).filter((e:Record<string,string>)=>['APPROVE','DECLINE'].includes(e.action));
          return {...u, creditScore: cs?.data?.score||0, riskBand: cs?.data?.risk_band||'N/A', decisions};
        } catch { return u; }
      }));
      setHistory(enriched);
    } catch { setHistory([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ load(); }, [load]);

  return (
    <div>
      <div className='flex items-center justify-between mb-4'>
        <h2 className='text-lg font-bold text-gray-900'>Decision History</h2>
        <button onClick={load} className='text-sm font-medium' style={{color:'#00544E'}}>Refresh</button>
      </div>
      {loading && <div className='flex justify-center py-10'><Spinner/></div>}
      {!loading && history.length===0 && <div className='text-center py-12 text-gray-400'>No decisions recorded yet.</div>}
      <div className='space-y-3'>
        {history.map((u,i)=>{
          const decs = (u.decisions as Array<Record<string,string>>)||[];
          const lastDec = decs[decs.length-1];
          return (
            <div key={i} className='border border-gray-200 rounded-xl overflow-hidden'>
              <div className='p-4 flex items-center justify-between'>
                <div className='flex items-center gap-4'>
                  <div>
                    <p className='font-bold text-gray-900'>{u.application_id as string}</p>
                    <p className='text-sm text-gray-500'>{u.market as string} - {(u.started_at as string)?.slice(0,10)}</p>
                  </div>
                  <div className='text-center'>
                    <p className='text-xs text-gray-500'>Score</p>
                    <p className='font-semibold text-gray-800'>{u.creditScore as number}/1000</p>
                  </div>
                  <div className='text-center'>
                    <p className='text-xs text-gray-500'>Risk</p>
                    <p className='font-semibold text-gray-800'>{u.riskBand as string}</p>
                  </div>
                </div>
                {lastDec && (
                  <span className={'font-bold px-4 py-1.5 rounded-full text-sm '+(lastDec.action==='APPROVE'?'bg-green-100 text-green-700':'bg-red-100 text-red-700')}>
                    {lastDec.action}
                  </span>
                )}
              </div>
              {decs.length>0 && (
                <div className='border-t border-gray-100 px-4 py-2 bg-gray-50 text-xs text-gray-500'>
                  {decs.map((d,j)=>(
                    <span key={j} className='mr-4'>{d.action} by {d.actor} on {d.timestamp?.slice(0,16).replace('T',' ')}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// =================== MAIN ASSESSOR PORTAL ===================
export default function AssessorPortal() {
  const [auth, setAuth] = useState(false);
  const [tab, setTab] = useState<'queue'|'summary'|'decision'|'history'>('queue');
  const [selectedAppId, setSelectedAppId] = useState('');

  if (!auth) return <LoginScreen onLogin={()=>setAuth(true)}/>;

  const TABS = [
    {id:'queue',label:'Decision Queue'},
    {id:'summary',label:'Application Summary'},
    {id:'decision',label:'Loan Decision'},
    {id:'history',label:'Decision History'},
  ] as const;

  const selectApp = (id: string) => { setSelectedAppId(id); setTab('summary'); };
  const proceedToDecision = (id: string) => { setSelectedAppId(id); setTab('decision'); };

  return (
    <div className='min-h-screen bg-gray-50'>
      <header className='bg-teal-700 text-white shadow-lg'>
        <div className='max-w-7xl mx-auto px-6 py-4 flex items-center justify-between'>
          <div>
            <h1 className='text-xl font-bold'>IPF Credit Assessor Portal</h1>
            <p className='text-teal-200 text-sm'>Credit Assessment and Loan Decision</p>
          </div>
          <div className='flex items-center gap-4'>
            <Link href='/' className='text-green-200 hover:text-white text-sm'>All Portals</Link>
            <button onClick={()=>setAuth(false)} className='text-green-200 hover:text-white text-sm border border-green-600 px-3 py-1 rounded'>Logout</button>
          </div>
        </div>
      </header>

      <div className='max-w-7xl mx-auto px-6 py-6'>
        <div className='flex gap-1 mb-6 border-b border-gray-200 overflow-x-auto'>
          {TABS.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)}
              className={'px-5 py-3 font-medium text-sm rounded-t-lg transition-colors whitespace-nowrap '+(tab===t.id?'bg-white border-t border-x border-gray-200 text-teal-700 -mb-px':'text-gray-500 hover:text-gray-700')}>
              {t.label}
            </button>
          ))}
        </div>

        <div className='bg-white rounded-2xl shadow-sm p-6'>
          {tab==='queue' && <DecisionQueueTab onSelectApp={selectApp}/>}
          {tab==='summary' && <AppSummaryTab initialAppId={selectedAppId} onProceedToDecision={proceedToDecision}/>}
          {tab==='decision' && <LoanDecisionTab initialAppId={selectedAppId}/>}
          {tab==='history' && <DecisionHistoryTab/>}
        </div>
      </div>
    </div>
  );
}
