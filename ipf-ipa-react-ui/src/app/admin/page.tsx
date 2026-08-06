"use client";
import { useState } from "react";
import { api, endpoints } from "@/lib/api";
import Link from "next/link";

const MARKETS = [
  { label: "Poland (PL)", value: "PL" },
  { label: "Romania (RO)", value: "RO" },
  { label: "Hungary (HU)", value: "HU" },
  { label: "Czech Republic (CZ)", value: "CZ" },
];

const DOC_TYPES: Record<string, string[]> = {
  PL: ["identity_card", "proof_of_address", "income_proof", "bank_statement"],
  RO: ["identity_document", "proof_of_address", "income_proof", "bank_statement", "other"],
  HU: ["identity_card", "address_card", "income_proof", "bank_account_documents"],
  CZ: ["identity_card", "income_proof", "proof_of_residence", "bank_statement", "evidence_of_expenses", "parameter_r"],
};

function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = () => {
    if (password === (process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "ipf-admin-2026")) {
      onLogin();
    } else {
      setError("Invalid password. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{background:"linear-gradient(160deg,#00544E,#003D39)"}}>
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4" style={{background:"#E8F5E9"}}>
            <svg className="w-8 h-8" style={{color:"#00544E"}} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg mx-auto mb-2" style={{background:"#00544E",color:"#7DC242"}}>IPF</div><h1 className="text-2xl font-bold text-gray-900">Admin Portal</h1>
          <p className="text-gray-500 mt-1 text-sm">International Personal Finance</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Admin Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#00544E]"
              placeholder="Enter password"
            />
          </div>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <button
            onClick={handleLogin}
            className="w-full text-white font-semibold py-3 rounded-lg transition-colors" style={{background:"#00544E"}}
          >
            Login
          </button>
          <Link href="/" className="block text-center text-sm text-gray-500 hover:text-gray-700">
            Back to Portal Selection
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function AdminPortal() {
  const [authenticated, setAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState<"upload" | "history" | "status">("upload");

  const [applicationId, setApplicationId] = useState("");
  const [market, setMarket] = useState("PL");
  const [loanAppFile, setLoanAppFile] = useState<File | null>(null);
  const [supportingFiles, setSupportingFiles] = useState<File[]>([]);
  const [docTypes, setDocTypes] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string; details?: string } | null>(null);

  const [history, setHistory] = useState<Record<string, string>[]>([]);
  const [statusAppId, setStatusAppId] = useState("");
  const [statusData, setStatusData] = useState<Record<string, unknown> | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  if (!authenticated) {
    return <LoginScreen onLogin={() => setAuthenticated(true)} />;
  }

  const handleSupportingFilesChange = (files: FileList | null) => {
    if (!files) return;
    const arr = Array.from(files);
    setSupportingFiles(arr);
    setDocTypes(arr.map(() => DOC_TYPES[market][0]));
  };

  const handleDocTypeChange = (index: number, value: string) => {
    const updated = [...docTypes];
    updated[index] = value;
    setDocTypes(updated);
  };

  const handleMarketChange = (m: string) => {
    setMarket(m);
    setDocTypes(supportingFiles.map(() => DOC_TYPES[m][0]));
  };

  const handleSubmit = async () => {
    if (!applicationId) { alert("Please enter a Loan Application ID"); return; }
    const allFiles = loanAppFile ? [loanAppFile, ...supportingFiles] : [...supportingFiles];
    const allTypes = loanAppFile ? ["loan_application", ...docTypes] : [...docTypes];
    if (allFiles.length === 0) { alert("Please select at least one document"); return; }

    setUploading(true);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append("application_id", applicationId);
      formData.append("market", market);
      formData.append("document_types", allTypes.join(","));
      formData.append("uploaded_by", "admin");
      allFiles.forEach((f) => formData.append("files", f));

      const resp = await api.post(endpoints.upload, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000,
      });
      setUploadResult({
        success: true,
        message: `${allFiles.length} document(s) uploaded successfully`,
        details: `Batch ID: ${resp.data.batch_id} | AI processing started automatically`,
      });
      setApplicationId("");
      setLoanAppFile(null);
      setSupportingFiles([]);
      setDocTypes([]);
    } catch (err: unknown) {
      const message = (err as Error).message || "Upload failed";
      setUploadResult({ success: false, message: `Upload failed: ${message}` });
    } finally {
      setUploading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const resp = await api.get(endpoints.uploadHistory);
      setHistory(resp.data.uploads || []);
    } catch {
      setHistory([]);
    }
  };

  const checkStatus = async () => {
    if (!statusAppId) return;
    setLoadingStatus(true);
    try {
      const resp = await api.get(endpoints.status(statusAppId));
      setStatusData(resp.data);
    } catch {
      setStatusData(null);
    } finally {
      setLoadingStatus(false);
    }
  };

  const statusBadge: Record<string, string> = {
    DECIDED: "bg-green-100 text-green-800",
    PENDING_REVIEW: "bg-yellow-100 text-yellow-800",
    PENDING_DECISION: "bg-orange-100 text-orange-800",
    PROCESSING: "bg-blue-100 text-blue-800",
    FAILED: "bg-red-100 text-red-800",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="text-white shadow-lg" style={{background:"linear-gradient(135deg,#00544E,#006E66)"}}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">IPF Admin Portal</h1>
            <p className="text-green-200 text-sm">Document Upload and Processing</p>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/" className="text-green-200 hover:text-white text-sm">All Portals</Link>
            <button onClick={() => setAuthenticated(false)} className="text-green-200 hover:text-white text-sm border border-green-600 px-3 py-1 rounded">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6">
        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {(["upload", "history", "status"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); if (tab === "history") loadHistory(); }}
              className={`px-5 py-3 font-medium text-sm rounded-t-lg transition-colors ${
                activeTab === tab ? "bg-white border-t border-x border-gray-200 text-[#00544E] -mb-px" : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "upload" ? "Upload Documents" : tab === "history" ? "Upload History" : "Processing Status"}
            </button>
          ))}
        </div>

        {activeTab === "upload" && (
          <div className="bg-white rounded-2xl shadow-sm p-8 max-w-3xl">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Upload New Documents</h2>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loan Application ID</label>
                <input
                  type="text"
                  value={applicationId}
                  onChange={(e) => setApplicationId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#00544E]"
                  placeholder="e.g. APP-PL-001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Market</label>
                <select value={market} onChange={(e) => handleMarketChange(e.target.value)} className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#00544E]">
                  {MARKETS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>
            </div>

            <div className="mb-6 p-5 border-2 border-dashed border-blue-200 rounded-xl bg-blue-50">
              <h3 className="font-semibold text-gray-800 mb-1">Step 1 - Loan Application Form</h3>
              <p className="text-sm text-gray-500 mb-3">Upload the customer signed loan application form (single PDF or image)</p>
              <input type="file" accept=".jpg,.jpeg,.png,.pdf,.tiff,.tif"
                onChange={(e) => setLoanAppFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:font-semibold file:text-white hover:file:opacity-90"
              />
              {loanAppFile && <p className="mt-2 text-sm text-blue-700 font-medium">Selected: {loanAppFile.name}</p>}
            </div>

            <div className="mb-6 p-5 border-2 border-dashed border-emerald-200 rounded-xl bg-emerald-50">
              <h3 className="font-semibold text-gray-800 mb-1">Step 2 - Supporting Documents</h3>
              <p className="text-sm text-gray-500 mb-3">Upload identity, address, income and bank documents (multiple files allowed)</p>
              <input type="file" accept=".jpg,.jpeg,.png,.pdf,.tiff,.tif" multiple
                onChange={(e) => handleSupportingFilesChange(e.target.files)}
                className="block w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-700"
              />
              {supportingFiles.length > 0 && (
                <div className="mt-3 space-y-2">
                  {supportingFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-3 bg-white p-2 rounded-lg">
                      <span className="text-sm text-gray-700 flex-1 truncate">{f.name}</span>
                      <select value={docTypes[i] || DOC_TYPES[market][0]} onChange={(e) => handleDocTypeChange(i, e.target.value)}
                        className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#00544E]">
                        {DOC_TYPES[market].map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
                      </select>
                      <span className="text-xs text-gray-400 whitespace-nowrap">{(f.size / 1024).toFixed(0)} KB</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {uploadResult && (
              <div className={`mb-4 p-4 rounded-lg ${uploadResult.success ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"}`}>
                <p className={`font-medium ${uploadResult.success ? "text-green-800" : "text-red-800"}`}>{uploadResult.message}</p>
                {uploadResult.details && <p className="text-sm text-gray-600 mt-1">{uploadResult.details}</p>}
              </div>
            )}

            <button onClick={handleSubmit} disabled={uploading || !applicationId}
              className="w-full text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2" style={{background:"#00544E"}}>
              {uploading ? (
                <><svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Uploading...</>
              ) : "Submit for AI Processing"}
            </button>
          </div>
        )}

        {activeTab === "history" && (
          <div className="bg-white rounded-2xl shadow-sm p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Upload History</h2>
              <button onClick={loadHistory} className="text-sm text-blue-600 hover:text-blue-800">Refresh</button>
            </div>
            {history.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg mb-2">No uploads found</p>
                <p className="text-gray-400 text-sm">Submit documents to see history here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((u, i) => (
                  <div key={i} className="border border-gray-200 rounded-xl p-4 flex items-center justify-between hover:bg-gray-50">
                    <div>
                      <p className="font-semibold text-gray-900">{u.application_id}</p>
                      <p className="text-sm text-gray-500">{u.market} &bull; {u.started_at?.slice(0, 10)}</p>
                    </div>
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full ${statusBadge[u.status] || "bg-gray-100 text-gray-700"}`}>{u.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "status" && (
          <div className="bg-white rounded-2xl shadow-sm p-8 max-w-2xl">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Processing Status</h2>
            <div className="flex gap-3 mb-6">
              <input type="text" value={statusAppId} onChange={(e) => setStatusAppId(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && checkStatus()}
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#00544E]"
                placeholder="Enter Application ID e.g. APP-PL-001" />
              <button onClick={checkStatus} disabled={loadingStatus}
                className="text-white font-semibold px-5 py-2 rounded-lg transition-colors disabled:bg-gray-300" style={{background:"#00544E"}}>
                {loadingStatus ? "Checking..." : "Check"}
              </button>
            </div>
            {statusData && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-gray-900 text-lg">{statusData.application_id as string}</span>
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full ${statusBadge[(statusData.workflow_status as string) || ""] || "bg-gray-100 text-gray-700"}`}>
                    {statusData.workflow_status as string}
                  </span>
                </div>
                <div className="space-y-2">
                  {((statusData.documents as Array<Record<string, string>>) || []).map((d, i) => (
                    <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50">
                      <span className="text-sm text-gray-700">{d.filename} <span className="text-gray-400">({d.type?.replace(/_/g, " ")})</span></span>
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${d.status === "VERIFIED" ? "bg-green-100 text-green-700" : d.status === "PROCESSING" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}`}>{d.status}</span>
                    </div>
                  ))}
                </div>
                {(() => { const rec = statusData.recommendation as string|undefined; return rec ? (
                    <div className={"p-4 rounded-xl font-semibold text-center " + (rec === "APPROVE" ? "bg-green-50 text-green-800 border border-green-200" : rec === "DECLINE" ? "bg-red-50 text-red-800 border border-red-200" : "bg-yellow-50 text-yellow-800 border border-yellow-200")}>
                      AI Recommendation: {rec}
                    </div>
                  ) : null; })()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
