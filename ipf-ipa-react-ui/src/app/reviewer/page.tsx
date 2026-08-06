"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import Link from "next/link";



interface QueueItem {
  id: string; filename?: string; original_filename?: string;
  type?: string; document_type?: string; status: string;
  application_id?: string; market?: string; uploaded_at?: string;
}
interface Extraction {
  id: string; field_name: string; extracted_value: string;
  corrected_value?: string; confidence: number;
  validation_status: string; validation_reason?: string;
}
interface DocReview {
  document_id: string; document_type: string; market: string;
  original_filename: string; image_b64?: string; content_type: string;
  status: string; extractions: Extraction[];
}
interface Discrepancy {
  id: string; label: string; status: string; severity: string;
  declared_value: string; extracted_value: string; detail: string;
  source_document_type?: string; override_explanation?: string; override_by?: string;
}
interface AuditEvent { id: string; action: string; actor: string; timestamp: string; details?: Record<string,unknown>; }

function Spinner() {
  return (
    <svg className="animate-spin w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
  );
}
function Badge({ status }: { status: string }) {
  const m: Record<string,string> = {
    MATCH:"bg-green-100 text-green-800", MISMATCH:"bg-red-100 text-red-800",
    WARNING:"bg-amber-100 text-amber-800", VERIFIED:"bg-green-100 text-green-800",
    PENDING_REVIEW:"bg-yellow-100 text-yellow-800", PROCESSING:"bg-blue-100 text-blue-800",
    FAILED:"bg-red-100 text-red-800", DECIDED:"bg-green-100 text-green-800",
    UNVERIFIABLE:"bg-gray-100 text-gray-600", EXTRACTED:"bg-purple-100 text-purple-700",
  };
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${m[status]||"bg-gray-100 text-gray-700"}`}>{status}</span>;
}
function ConfBadge({ v }: { v: number }) {
  const p = v >= 1 ? Math.round(v) : Math.round(v*100);
  const c = p>=85?"bg-green-100 text-green-800":p>=70?"bg-amber-100 text-amber-800":"bg-red-100 text-red-800";
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${c}`}>{p}%</span>;
}

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [pw, setPw] = useState(""); const [err, setErr] = useState("");
  const login = () => {
    if (pw === (process.env.NEXT_PUBLIC_REVIEWER_PASSWORD || "ipf-reviewer-2026")) { onLogin(); }
    else { setErr("Invalid password."); }
  };
  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{background:"linear-gradient(160deg,#00544E,#003D39)"}}>
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" style={{background:"#E8F5E9"}}>
            <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
            </svg>
          </div>
          <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg mx-auto mb-2" style={{background:"#00544E",color:"#7DC242"}}>IPF</div><h1 className="text-2xl font-bold text-gray-900">Reviewer Portal</h1>
          <p className="text-gray-500 mt-1">IPF Intelligent Process Automation</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reviewer Password</label>
            <input type="password" value={pw} onChange={e=>setPw(e.target.value)}
              onKeyDown={e=>e.key==="Enter"&&login()}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
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

// =================== WORK QUEUE TAB ===================
function WorkQueueTab({ onOpenDoc, onOpenApp }: { onOpenDoc: (id:string)=>void; onOpenApp: (id:string)=>void }) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('All');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter !== 'All' ? { status: filter } : {};
      const r = await api.get('/api/queue', { params });
      setItems(r.data.items || []);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const grouped: Record<string, QueueItem[]> = {};
  items.forEach(item => {
    const key = item.application_id || 'unknown';
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(item);
  });

  return (
    <div>
      <div className='flex items-center justify-between mb-4'>
        <h2 className='text-lg font-bold text-gray-900'>Work Queue</h2>
        <div className='flex gap-3 items-center'>
          <select value={filter} onChange={e=>setFilter(e.target.value)} className='text-sm border border-gray-300 rounded-lg px-3 py-1.5'>
            {['All','PENDING_REVIEW','EXTRACTED','VERIFIED'].map(s=><option key={s}>{s}</option>)}
          </select>
          <button onClick={load} className='text-sm font-medium' style={{color:'#00544E'}}>Refresh</button>
        </div>
      </div>
      {loading && <div className='flex justify-center py-10'><Spinner/></div>}
      {!loading && Object.keys(grouped).length === 0 && (
        <div className='text-center py-12 text-gray-400'>No items in queue.</div>
      )}
      {!loading && Object.entries(grouped).map(([appId, docs]) => (
        <div key={appId} className='mb-5 border border-gray-200 rounded-xl overflow-hidden shadow-sm'>
          <div className='bg-emerald-50 px-4 py-3 flex items-center justify-between'>
            <span className='font-semibold text-emerald-800'>Application: {appId}</span>
            <div className='flex items-center gap-3'>
              <span className='text-sm text-gray-500'>{docs[0]?.market} - {docs.length} doc(s)</span>
              <button onClick={()=>onOpenApp(appId)} className='text-white text-xs font-semibold px-3 py-1.5 rounded-lg' style={{background:'#00544E'}}>Review Application</button>
            </div>
          </div>
          <table className='w-full text-sm'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='text-left px-4 py-2 font-medium text-gray-600'>Filename</th>
                <th className='text-left px-4 py-2 font-medium text-gray-600'>Type</th>
                <th className='text-left px-4 py-2 font-medium text-gray-600'>Status</th>
                <th className='text-left px-4 py-2 font-medium text-gray-600'>Action</th>
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.id} className='border-t border-gray-100 hover:bg-gray-50'>
                  <td className='px-4 py-3 text-gray-800 truncate max-w-xs'>{doc.original_filename||doc.filename||doc.id}</td>
                  <td className='px-4 py-3 text-gray-500'>{(doc.document_type||doc.type||'').replace(/_/g,' ')}</td>
                  <td className='px-4 py-3'><Badge status={doc.status}/></td>
                  <td className='px-4 py-3'>
                    <button onClick={()=>onOpenDoc(doc.id)} className='text-xs font-semibold underline' style={{color:'#00544E'}}>Open Doc</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

// =================== REVIEW DOCUMENT TAB ===================
function ReviewDocTab({ initialDocId, reviewerId }: { initialDocId: string; reviewerId: string }) {
  const [inputId, setInputId] = useState(initialDocId);
  const [data, setData] = useState<DocReview|null>(null);
  const [loading, setLoading] = useState(false);
  const [corrections, setCorrections] = useState<Record<string,string>>({});
  const [msg, setMsg] = useState('');

  const loadDoc = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true); setMsg(''); setData(null); setCorrections({});
    try {
      const r = await api.get('/api/review/'+id);
      setData(r.data);
    } catch { setMsg('Document not found or backend unavailable.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { if (initialDocId) { setInputId(initialDocId); loadDoc(initialDocId); } }, [initialDocId, loadDoc]);

  const submitCorrections = async () => {
    if (!data || Object.keys(corrections).length === 0) return;
    try {
      const payload = Object.entries(corrections).map(([eid, val]) => ({ extraction_id: eid, corrected_value: val, corrected_by: reviewerId }));
      await api.post('/api/review/'+data.document_id+'/correct', payload);
      setMsg('Corrections saved.'); setCorrections({}); loadDoc(data.document_id);
    } catch { setMsg('Failed to save corrections.'); }
  };

  const confirmDoc = async () => {
    if (!data) return;
    try {
      await api.post('/api/review/'+data.document_id+'/confirm', null, { params: { reviewer_id: reviewerId } });
      setMsg('Document confirmed as verified.'); loadDoc(data.document_id);
    } catch { setMsg('Failed to confirm.'); }
  };

  return (
    <div>
      <div className='flex gap-3 mb-6'>
        <input type='text' value={inputId} onChange={e=>setInputId(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&loadDoc(inputId)}
          className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400'
          placeholder='Enter Document ID'/>
        <button onClick={()=>loadDoc(inputId)} className='bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2 rounded-lg'>Load</button>
      </div>
      {loading && <div className='flex justify-center py-12'><Spinner/></div>}
      {msg && <div className={'mb-4 p-3 rounded-lg text-sm font-medium '+(msg.includes('saved')||msg.includes('confirmed')?'bg-green-50 text-green-800 border border-green-200':'bg-red-50 text-red-800 border border-red-200')}>{msg}</div>}
      {data && (
        <div>
          <div className='flex items-center gap-3 mb-4'>
            <h2 className='text-lg font-bold text-gray-900'>{data.document_type.replace(/_/g,' ')}</h2>
            <Badge status={data.status}/>
            <span className='text-sm text-gray-500'>{data.market} - {data.original_filename}</span>
          </div>
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            <div className='bg-gray-50 rounded-xl p-4'>
              <h3 className='font-semibold text-gray-700 mb-3'>Original Document Preview</h3>
              {data.image_b64 ? (
                data.content_type?.includes('pdf') ? (
                  <div className='space-y-2'>
                    <img src={process.env.NEXT_PUBLIC_API_URL+'/api/document/'+data.document_id+'/preview'} alt='PDF Preview' className='rounded-lg border border-gray-200 w-full'/>
                    <a href={'data:application/pdf;base64,'+data.image_b64} download={data.original_filename} className='text-sm text-emerald-600 underline'>Download PDF</a>
                  </div>
                ) : (
                  <img src={'data:'+data.content_type+';base64,'+data.image_b64} alt='Document' className='rounded-lg border border-gray-200 w-full'/>
                )
              ) : (
                <div className='text-gray-400 text-center py-12 bg-white rounded-lg border border-gray-200'>No preview available</div>
              )}
            </div>
            <div>
              <div className='flex items-center justify-between mb-3'>
                <h3 className='font-semibold text-gray-700'>AI Extracted Fields ({data.extractions.length})</h3>
                <div className='flex gap-2'>
                  <span className='text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full'>{data.extractions.filter(e=>e.confidence>=85).length} high</span>
                  <span className='text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full'>{data.extractions.filter(e=>e.confidence<70).length} low</span>
                </div>
              </div>
              <div className='space-y-2 max-h-96 overflow-y-auto pr-1'>
                {data.extractions.map(ext => {
                  const current = corrections[ext.id] ?? (ext.corrected_value || ext.extracted_value || '');
                  const original = ext.corrected_value || ext.extracted_value || '';
                  return (
                    <div key={ext.id} className='bg-white border border-gray-200 rounded-lg p-3'>
                      <div className='flex items-center gap-2 mb-1'>
                        <span className='text-xs font-semibold text-gray-600'>{ext.field_name.replace(/_/g,' ')}</span>
                        <ConfBadge v={ext.confidence}/>
                        <Badge status={ext.validation_status||'PENDING'}/>
                      </div>
                      <input type='text' value={current} onChange={e=>setCorrections(prev=>({...prev,[ext.id]:e.target.value}))}
                        className={'w-full text-sm border rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-400 '+(corrections[ext.id]&&corrections[ext.id]!==original?'border-amber-400 bg-amber-50':'border-gray-200')}/>
                      {ext.validation_status==='FAIL'&&ext.validation_reason&&<p className='text-xs text-red-600 mt-1'>{ext.validation_reason}</p>}
                    </div>
                  );
                })}
              </div>
              {/* Confidence Summary */}
              <div className='mt-3 grid grid-cols-3 gap-2 text-center'>
                <div className='bg-green-50 border border-green-200 rounded-lg p-2'>
                  <div className='text-lg font-bold text-green-700'>{data.extractions.filter(e=>e.confidence>=85).length}</div>
                  <div className='text-xs text-green-600'>High Confidence</div>
                  <div className='text-xs text-gray-400'>85%+</div>
                </div>
                <div className='bg-amber-50 border border-amber-200 rounded-lg p-2'>
                  <div className='text-lg font-bold text-amber-700'>{data.extractions.filter(e=>e.confidence>=70&&e.confidence<85).length}</div>
                  <div className='text-xs text-amber-600'>Medium Confidence</div>
                  <div className='text-xs text-gray-400'>70-84%</div>
                </div>
                <div className='bg-red-50 border border-red-200 rounded-lg p-2'>
                  <div className='text-lg font-bold text-red-700'>{data.extractions.filter(e=>e.confidence<70).length}</div>
                  <div className='text-xs text-red-600'>Low Confidence</div>
                  <div className='text-xs text-gray-400'>Below 70%</div>
                </div>
              </div>
              <div className='flex gap-3 mt-4'>
                {Object.keys(corrections).length>0&&(
                  <button onClick={submitCorrections} className='flex-1 bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2 rounded-lg text-sm'>
                    Submit {Object.keys(corrections).length} Correction(s)
                  </button>
                )}
                <button onClick={confirmDoc} className='flex-1 text-white font-semibold py-2.5 rounded-lg text-sm font-bold' style={{background:'#00544E'}}>
                  Approve Document
                </button>
                <button onClick={async()=>{
                  try {
                    await api.post('/api/review/'+data.document_id+'/confirm', null, { params: { reviewer_id: reviewerId } });
                    setMsg('Document flagged for further review.');
                    loadDoc(data.document_id);
                  } catch { setMsg('Failed.'); }
                }} className='flex-1 text-white font-semibold py-2.5 rounded-lg text-sm font-bold' style={{background:'#b91c1c'}}>
                  Reject Document
                </button>
              </div>
              <p className='text-xs text-gray-400 mt-2 text-center'>Approve = confirms all fields correct and marks document as VERIFIED. Reject = flags document for re-submission.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =================== APPLICATION REVIEW TAB ===================
function AppReviewTab({ initialAppId, reviewerId, onOpenDoc }: { initialAppId: string; reviewerId: string; onOpenDoc: (id:string)=>void }) {
  const [appId, setAppId] = useState(initialAppId);
  const [inputId, setInputId] = useState(initialAppId);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Record<string,unknown>|null>(null);
  const [loanApp, setLoanApp] = useState<Record<string,unknown>|null>(null);
  const [discData, setDiscData] = useState<{summary:Record<string,number>;discrepancies:Discrepancy[]}|null>(null);
  const [overrideMsg, setOverrideMsg] = useState('');

  const loadApp = useCallback(async (id: string) => {
    if (!id) return;
    setLoading(true); setStatus(null); setLoanApp(null); setDiscData(null);
    try {
      const [sr, lr, dr] = await Promise.all([
        api.get('/api/status/'+id).catch(()=>null),
        api.get('/api/loan-application/'+id).catch(()=>null),
        api.get('/api/discrepancies/'+id).catch(()=>null),
      ]);
      if (sr) setStatus(sr.data);
      if (lr) setLoanApp(lr.data);
      if (dr) setDiscData(dr.data);
    } catch { /* handled per-request */ }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{ if (initialAppId) { setAppId(initialAppId); setInputId(initialAppId); loadApp(initialAppId); } }, [initialAppId, loadApp]);

  const submitOverride = async (discId: string, explanation: string) => {
    try {
      await api.post('/api/discrepancies/'+appId+'/override', { discrepancy_id: discId, explanation, override_by: reviewerId });
      setOverrideMsg('Discrepancy marked as reviewed.'); loadApp(appId);
    } catch { setOverrideMsg('Override failed.'); }
  };

  const docs = (status?.documents as Array<Record<string,string>>) || [];
  const verified = docs.filter(d=>d.status==='VERIFIED').length;
  const disc = discData?.discrepancies || [];
  const dsum = discData?.summary || {};
  const fields = (loanApp as Record<string,Record<string,{value?:string}|string>>)?.extracted_fields || {};

  const FIELD_DISPLAY: Record<string,string> = {
    applicant_full_name:'Full Name', date_of_birth:'Date of Birth', residential_address:'Address',
    declared_net_monthly_income:'Declared Income', declared_income_currency:'Currency',
    requested_loan_amount:'Loan Amount', loan_term_weeks:'Loan Term (weeks)',
    employment_status:'Employment', employer_name:'Employer',
    bank_account_number:'Bank Account', purpose_of_loan:'Purpose',
  };
  const fieldStatusMap: Record<string,string> = {};
  disc.forEach(d => { if (d.label) fieldStatusMap[d.label.toLowerCase().replace(/ /g,'_')] = d.status; });

  return (
    <div>
      <div className='flex gap-3 mb-6'>
        <input type='text' value={inputId} onChange={e=>setInputId(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&(()=>{setAppId(inputId);loadApp(inputId);})()}
          className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400'
          placeholder='Enter Application ID e.g. APP-PL-GOOD-001'/>
        <button onClick={()=>{setAppId(inputId);loadApp(inputId);}} className='bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2 rounded-lg'>Load</button>
      </div>
      {loading && <div className='flex justify-center py-12'><Spinner/></div>}
      {overrideMsg && <div className='mb-4 p-3 rounded-lg text-sm font-medium bg-green-50 text-green-800 border border-green-200'>{overrideMsg}</div>}

      {status && (
        <div>
          {/* Summary Banner */}
          <div className='grid grid-cols-4 gap-4 mb-6'>
            {[
              {label:'Documents',value:docs.length,sub:'total'},
              {label:'Verified',value:verified,sub:'of '+docs.length,ok:verified===docs.length},
              {label:'Mismatches',value:dsum.mismatches||0,sub:'cross-ref',warn:(dsum.mismatches||0)>0},
              {label:'High Risk',value:dsum.high_severity||0,sub:'flags',err:(dsum.high_severity||0)>0},
            ].map(m=>(
              <div key={m.label} className={'rounded-xl p-4 text-center border '+(m.err?'bg-red-50 border-red-200':m.warn?'bg-amber-50 border-amber-200':m.ok?'bg-green-50 border-green-200':'bg-white border-gray-200')}>
                <div className={'text-2xl font-bold '+(m.err?'text-red-700':m.warn?'text-amber-700':m.ok?'text-green-700':'text-gray-800')}>{m.value}</div>
                <div className='text-xs font-semibold text-gray-600 mt-0.5'>{m.label}</div>
                <div className='text-xs text-gray-400'>{m.sub}</div>
              </div>
            ))}
          </div>

          {/* PANEL A - Loan Application */}
          <div className='bg-white border border-gray-200 rounded-xl mb-6 overflow-hidden'>
            <div className='px-5 py-3 border-b border-gray-200' style={{background:'#E8F7F5'}}>
              <h3 className='font-bold' style={{color:'#00544E'}}>Panel A - Loan Application (Customer Declared)</h3>
            </div>
            <div className='p-5'>
              {loanApp ? (
                <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
                  <div>
                    <h4 className='font-semibold text-gray-700 mb-3'>Document Preview</h4>
                    {docs.find(d=>d.type==='loan_application') ? (
                      <div>
                        <img src={process.env.NEXT_PUBLIC_API_URL+'/api/document/'+docs.find(d=>d.type==='loan_application')?.id+'/preview'}
                          alt='Loan Application' className='rounded-lg border border-gray-200 w-full shadow-sm mb-3'/>
                        <button onClick={()=>onOpenDoc(docs.find(d=>d.type==='loan_application')?.id||'')}
                          className='w-full text-white text-sm font-semibold py-2 rounded-lg flex items-center justify-center gap-2'
                          style={{background:'#00544E'}}>
                          <svg className='w-4 h-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'/>
                          </svg>
                          Review This Document
                        </button>
                      </div>
                    ) : (
                      <div className='text-gray-400 text-sm bg-gray-50 rounded-lg p-8 text-center border border-dashed border-gray-200'>No loan application document found</div>
                    )}
                  </div>
                  <div>
                    <h4 className='font-semibold text-gray-700 mb-3'>Declared Fields</h4>
                    <div className='space-y-2'>
                      {Object.entries(FIELD_DISPLAY).map(([key, label]) => {
                        const fd = fields[key];
                        const val = (typeof fd==='object'&&fd!==null&&'value' in fd) ? fd.value : (fd as string);
                        if (!val||val==='None') return null;
                        const cs = fieldStatusMap[key] || 'UNVERIFIABLE';
                        return (
                          <div key={key} className='flex items-start justify-between py-1.5 border-b border-gray-100'>
                            <span className='text-sm font-medium text-gray-600 w-40 shrink-0'>{label}</span>
                            <span className='text-sm text-gray-800 flex-1'>{val as string}</span>
                            {cs!=='UNVERIFIABLE'&&<Badge status={cs}/>}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className='text-amber-700 bg-amber-50 rounded-lg p-4 text-sm'>No loan application form found. Upload a loan_application document to enable cross-referencing.</div>
              )}
            </div>
          </div>

          {/* PANEL B - Supporting Documents */}
          <div className='bg-white border border-gray-200 rounded-xl mb-6 overflow-hidden'>
            <div className='px-5 py-3 border-b border-gray-200' style={{background:'#F0F9F7'}}>
              <h3 className='font-bold' style={{color:'#006E66'}}>Panel B - Supporting Documents & OCR Extractions</h3>
            </div>
            <div className='p-5'>
              {docs.filter(d=>d.type!=='loan_application').length===0 ? (
                <p className='text-gray-500 text-sm'>No supporting documents found.</p>
              ) : (
                <div className='space-y-3'>
                  {docs.filter(d=>d.type!=='loan_application').map(doc=>(
                    <SupportingDocRow key={doc.id} doc={doc} onOpenDoc={onOpenDoc}/>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* PANEL C - Discrepancies */}
          <div className='bg-white border border-gray-200 rounded-xl overflow-hidden'>
            <div className='bg-red-50 px-5 py-3 border-b border-gray-200'>
              <h3 className='font-bold text-red-800'>Panel C - Cross-Reference Discrepancy Report</h3>
            </div>
            <div className='p-5'>
              {disc.length===0 ? (
                <div className='text-green-700 bg-green-50 rounded-lg p-4 text-sm'>{loanApp?'No discrepancies found - all cross-checks passed.':'Cross-reference not available - no loan application uploaded.'}</div>
              ) : (
                <div>
                  <div className='grid grid-cols-4 gap-3 mb-4 text-center'>
                    {[{l:'Total',v:dsum.total||0},{l:'Mismatches',v:dsum.mismatches||0},{l:'Warnings',v:dsum.warnings||0},{l:'Matches',v:dsum.matches||0}].map(x=>(
                      <div key={x.l} className='bg-gray-50 rounded-lg p-3'>
                        <div className='text-xl font-bold text-gray-800'>{x.v}</div>
                        <div className='text-xs text-gray-500'>{x.l}</div>
                      </div>
                    ))}
                  </div>
                  <div className='space-y-3'>
                    {disc.map(d=>(
                      <DiscrepancyCard key={d.id} disc={d} onOverride={submitOverride}/>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Supporting Doc Row (used in Panel B) ---
function SupportingDocRow({ doc, onOpenDoc }: { doc: Record<string,string>; onOpenDoc: (id:string)=>void }) {
  const [open, setOpen] = useState(false);
  const [extData, setExtData] = useState<DocReview|null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true);
    if (extData) return;
    setLoading(true);
    try {
      const r = await api.get('/api/review/'+doc.id);
      setExtData(r.data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  return (
    <div className='border border-gray-200 rounded-xl overflow-hidden'>
      <div className='w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50'>
        <button onClick={load} className='flex items-center gap-3 text-left flex-1'>
          <Badge status={doc.status}/>
          <span className='font-medium text-gray-800'>{(doc.document_type||doc.type||'').replace(/_/g,' ')}</span>
          <span className='text-sm text-gray-500'>{doc.original_filename||doc.filename}</span>
        </button>
        <div className='flex items-center gap-2 flex-shrink-0'>
          <button onClick={()=>onOpenDoc(doc.id)}
            className='text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1'
            style={{background:'#00544E'}}>
            <svg className='w-3.5 h-3.5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'/>
            </svg>
            Review Document
          </button>
          <button onClick={load} className='p-1'>
            <svg className={'w-4 h-4 text-gray-400 transition-transform '+(open?'rotate-180':'')} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7'/>
            </svg>
          </button>
        </div>
      </div>
      {open && (
        <div className='border-t border-gray-200 p-4 bg-gray-50'>
          {loading && <div className='flex justify-center py-4'><Spinner/></div>}
          {extData && (
            <div className='grid grid-cols-1 lg:grid-cols-2 gap-4'>
              <div>
                {extData.image_b64 ? (
                  extData.content_type?.includes('pdf') ? (
                    <img src={process.env.NEXT_PUBLIC_API_URL+'/api/document/'+doc.id+'/preview'} alt='preview' className='rounded border border-gray-200 w-full'/>
                  ) : (
                    <img src={'data:'+extData.content_type+';base64,'+extData.image_b64} alt='doc' className='rounded border border-gray-200 w-full'/>
                  )
                ) : <div className='text-gray-400 text-sm p-4 text-center bg-white rounded-lg border'>No preview</div>}
              </div>
              <div>
                <div className='flex gap-2 mb-2'>
                  <span className='text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full'>{extData.extractions.length} fields</span>
                  <span className='text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full'>{extData.extractions.filter(e=>e.confidence>=85).length} high conf</span>
                </div>
                <div className='space-y-1.5 max-h-64 overflow-y-auto'>
                  {extData.extractions.map(e=>(
                    <div key={e.id} className='flex items-center justify-between bg-white px-3 py-1.5 rounded border border-gray-100'>
                      <span className='text-xs font-medium text-gray-600'>{e.field_name.replace(/_/g,' ')}</span>
                      <div className='flex items-center gap-2'>
                        <span className='text-xs text-gray-800'>{e.corrected_value||e.extracted_value}</span>
                        <ConfBadge v={e.confidence}/>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- Discrepancy Card ---
function DiscrepancyCard({ disc, onOverride }: { disc: Discrepancy; onOverride: (id:string,exp:string)=>void }) {
  const [exp, setExp] = useState('');
  const [showForm, setShowForm] = useState(false);
  const borderCls = disc.status==='MISMATCH'?'border-red-200 bg-red-50':disc.status==='WARNING'?'border-amber-200 bg-amber-50':disc.status==='MATCH'?'border-green-200 bg-green-50':'border-gray-200 bg-gray-50';

  return (
    <div className={'border rounded-xl p-4 '+borderCls}>
      <div className='flex items-center justify-between mb-2'>
        <div className='flex items-center gap-2'>
          <span className='font-semibold text-gray-800'>{disc.label}</span>
          <Badge status={disc.status}/>
          {disc.severity&&<span className='text-xs text-gray-500 bg-white border border-gray-200 px-1.5 py-0.5 rounded'>{disc.severity}</span>}
        </div>
        {disc.override_explanation&&<span className='text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full'>Reviewed</span>}
      </div>
      <div className='grid grid-cols-2 gap-4 mb-2'>
        <div><span className='text-xs font-medium text-gray-500'>Declared (Loan App)</span><div className='text-sm text-gray-800 mt-0.5'>{disc.declared_value||'-'}</div></div>
        <div><span className='text-xs font-medium text-gray-500'>Extracted (Document)</span><div className='text-sm text-gray-800 mt-0.5'>{disc.extracted_value||'-'}</div></div>
      </div>
      {disc.detail&&<p className='text-xs text-gray-600 mb-2'>{disc.detail}</p>}
      {disc.override_explanation ? (
        <div className='text-xs bg-green-100 text-green-800 rounded p-2'>Override: {disc.override_explanation} by {disc.override_by}</div>
      ) : disc.status!=='MATCH'&&disc.status!=='UNVERIFIABLE' ? (
        <div>
          {!showForm ? (
            <button onClick={()=>setShowForm(true)} className='text-xs text-blue-600 hover:text-blue-800 underline'>Mark as Reviewed</button>
          ) : (
            <div className='flex gap-2 mt-2'>
              <input type='text' value={exp} onChange={e=>setExp(e.target.value)} placeholder='Override explanation (required)'
                className='flex-1 text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400'/>
              <button onClick={()=>{if(exp){onOverride(disc.id,exp);setShowForm(false);}}} className='text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700'>Save</button>
              <button onClick={()=>setShowForm(false)} className='text-xs text-gray-500 px-2 py-1'>Cancel</button>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

// =================== AUDIT TRAIL TAB ===================
function AuditTrailTab({ initialAppId }: { initialAppId: string }) {
  const [inputId, setInputId] = useState(initialAppId);
  const [trail, setTrail] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const PIPELINE = [
    {key:'UPLOAD',label:'Documents Uploaded'},
    {key:'EXTRACT_LOAN_APP',label:'Loan App Extracted'},
    {key:'EXTRACT',label:'Documents Extracted'},
    {key:'CROSS_REFERENCE',label:'Cross-Reference Check'},
    {key:'PAUSE_FOR_REVIEW',label:'Pending Review'},
    {key:'CORRECT',label:'Field Corrections'},
    {key:'CONFIRM',label:'Document Confirmed'},
    {key:'RECOMMEND',label:'AI Recommendation'},
    {key:'APPROVE',label:'Loan Approved'},
    {key:'DECLINE',label:'Loan Declined'},
  ];

  const loadAudit = async (id: string) => {
    if (!id) return;
    setLoading(true); setLoaded(false);
    try {
      const r = await api.get('/api/audit/'+id);
      setTrail(r.data.audit_trail || []);
      setLoaded(true);
    } catch { setTrail([]); }
    finally { setLoading(false); }
  };

  useEffect(()=>{ if (initialAppId) { setInputId(initialAppId); loadAudit(initialAppId); } }, [initialAppId]);

  const completed = new Set(trail.map(e=>e.action));
  const failed = completed.has('WORKFLOW_FAILED');

  return (
    <div>
      <div className='flex gap-3 mb-6'>
        <input type='text' value={inputId} onChange={e=>setInputId(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&loadAudit(inputId)}
          className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-400'
          placeholder='Enter Application ID e.g. APP-PL-GOOD-001'/>
        <button onClick={()=>loadAudit(inputId)} className='bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-2 rounded-lg'>Load Audit Trail</button>
      </div>
      {loading && <div className='flex justify-center py-12'><Spinner/></div>}
      {loaded && (
        <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
          {/* Event Log */}
          <div className='lg:col-span-2'>
            <h3 className='font-bold text-gray-900 mb-3'>Event Log ({trail.length} events)</h3>
            {trail.length===0 ? (
              <div className='text-gray-400 text-sm p-4 bg-gray-50 rounded-lg text-center'>No audit events found.</div>
            ) : (
              <div className='space-y-2'>
                {trail.map((ev,i)=>(
                  <div key={ev.id||i} className='bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-start gap-3'>
                    <div className={'w-2 h-2 rounded-full mt-2 shrink-0 '+(ev.action==='APPROVE'?'bg-green-500':ev.action==='DECLINE'?'bg-red-500':ev.action==='WORKFLOW_FAILED'?'bg-red-500':'bg-blue-400')}/>
                    <div className='flex-1 min-w-0'>
                      <div className='flex items-center gap-2 flex-wrap'>
                        <span className='font-semibold text-gray-800 text-sm'>{ev.action}</span>
                        <span className='text-xs text-gray-500'>by {ev.actor}</span>
                        <span className='text-xs text-gray-400 ml-auto'>{ev.timestamp?.slice(0,19).replace('T',' ')}</span>
                      </div>
                      {ev.details&&Object.keys(ev.details).length>0&&(
                        <div className='mt-1 text-xs text-gray-500'>{JSON.stringify(ev.details).slice(0,120)}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Processing Flow Diagram */}
          <div>
            <h3 className='font-bold text-gray-900 mb-3'>Processing Flow</h3>
            <div className='space-y-1'>
              {PIPELINE.map((step,i)=>{
                const done = completed.has(step.key);
                const isDecline = step.key==='DECLINE';
                const isApprove = step.key==='APPROVE';
                const bg = done?(isApprove?'bg-green-500':isDecline?'bg-red-500':'bg-emerald-500'):'bg-gray-200';
                const textColor = done?'text-white':'text-gray-500';
                const labelColor = done?'text-gray-900 font-semibold':'text-gray-400';
                return (
                  <div key={step.key} className='flex items-center gap-3'>
                    <div className='flex flex-col items-center'>
                      <div className={'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold '+bg+' '+textColor}>
                        {done ? (
                          <svg className='w-4 h-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={3} d='M5 13l4 4L19 7'/>
                          </svg>
                        ) : (i+1)}
                      </div>
                      {i<PIPELINE.length-1&&<div className={'w-0.5 h-4 '+(done?'bg-emerald-400':'bg-gray-200')}/>}
                    </div>
                    <span className={'text-sm '+labelColor}>{step.label}</span>
                    {done&&<span className='ml-auto text-xs text-emerald-600 font-medium'>Done</span>}
                  </div>
                );
              })}
              {failed&&<div className='mt-2 bg-red-50 border border-red-200 rounded-lg p-2 text-xs text-red-700'>Workflow failed - check event log for details</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =================== MAIN REVIEWER PORTAL ===================
export default function ReviewerPortal() {
  const [auth, setAuth] = useState(false);
  const [tab, setTab] = useState<'queue'|'app-review'|'review-doc'|'audit'>('queue');
  const [selectedDocId, setSelectedDocId] = useState('');
  const [selectedAppId, setSelectedAppId] = useState('');
  const reviewerId = 'reviewer';

  if (!auth) return <LoginScreen onLogin={()=>setAuth(true)}/>;

  const TABS = [
    {id:'queue',label:'Work Queue'},
    {id:'app-review',label:'Application Review'},
    {id:'review-doc',label:'Review Document'},
    {id:'audit',label:'Audit Trail'},
  ] as const;

  const openDoc = (id: string) => { setSelectedDocId(id); setTab('review-doc'); };
  const openApp = (id: string) => { setSelectedAppId(id); setTab('app-review'); };

  return (
    <div className='min-h-screen bg-gray-50'>
      {/* Header */}
      <header className='bg-emerald-700 text-white shadow-lg'>
        <div className='max-w-7xl mx-auto px-6 py-4 flex items-center justify-between'>
          <div>
            <h1 className='text-xl font-bold'>IPF Reviewer Portal</h1>
            <p className='text-emerald-200 text-sm'>Document Review and Cross-Reference Verification</p>
          </div>
          <div className='flex items-center gap-4'>
            <Link href='/' className='text-green-200 hover:text-white text-sm'>All Portals</Link>
            <button onClick={()=>setAuth(false)} className='text-green-200 hover:text-white text-sm border border-green-600 px-3 py-1 rounded'>Logout</button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className='max-w-7xl mx-auto px-6 py-6'>
        <div className='flex gap-1 mb-6 border-b border-gray-200 overflow-x-auto'>
          {TABS.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)}
              className={'px-5 py-3 font-medium text-sm rounded-t-lg transition-colors whitespace-nowrap '+(tab===t.id?'bg-white border-t border-x border-gray-200 text-emerald-700 -mb-px':'text-gray-500 hover:text-gray-700')}>
              {t.label}
            </button>
          ))}
        </div>

        <div className='bg-white rounded-2xl shadow-sm p-6'>
          {tab==='queue' && <WorkQueueTab onOpenDoc={openDoc} onOpenApp={openApp}/>}
          {tab==='app-review' && <AppReviewTab initialAppId={selectedAppId} reviewerId={reviewerId} onOpenDoc={openDoc}/>}
          {tab==='review-doc' && <ReviewDocTab initialDocId={selectedDocId} reviewerId={reviewerId}/>}
          {tab==='audit' && <AuditTrailTab initialAppId={selectedAppId}/>}
        </div>
      </div>
    </div>
  );
}
