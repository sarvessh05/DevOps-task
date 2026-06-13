import React, { useState, useEffect, useCallback } from 'react';
import { 
  PlusCircle, 
  History, 
  LayoutDashboard, 
  Cpu, 
  Activity, 
  FileSpreadsheet, 
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Calendar,
  Layers
} from 'lucide-react';
import FileUpload from './components/FileUpload';
import JobProgress from './components/JobProgress';
import Dashboard from './components/Dashboard';
import TransactionTable from './components/TransactionTable';

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [jobsHistory, setJobsHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  // Processing state
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobError, setJobError] = useState(null);
  
  // Results state
  const [results, setResults] = useState(null);
  const [loadingResults, setLoadingResults] = useState(false);

  // 1. Fetch Job History
  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const response = await fetch("http://localhost:8000/jobs");
      if (response.ok) {
        const data = await response.json();
        setJobsHistory(data);
      }
    } catch (err) {
      console.error("Failed to fetch jobs history:", err);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // 2. Fetch Job Results
  const fetchResults = useCallback(async (jobId) => {
    if (!jobId) return;
    setLoadingResults(true);
    try {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}/results`);
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      } else {
        throw new Error("Failed to load results");
      }
    } catch (err) {
      console.error(err);
      setJobError("Error loading job details. Please try again.");
    } finally {
      setLoadingResults(false);
    }
  }, []);

  // 3. Polling Effect for active processing jobs
  useEffect(() => {
    if (!selectedJobId || (jobStatus !== 'pending' && jobStatus !== 'processing')) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${selectedJobId}/status`);
        if (!response.ok) throw new Error("Status fetch failed");
        
        const data = await response.json();
        setJobStatus(data.status);
        setJobProgress(data.progress);
        
        if (data.status === 'completed') {
          clearInterval(pollInterval);
          // Pull down full results and switch tabs
          await fetchResults(selectedJobId);
          setActiveTab('dashboard');
          fetchHistory();
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          setJobError(data.error_message || "Task failed execution.");
          fetchHistory();
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(pollInterval);
  }, [selectedJobId, jobStatus, fetchResults, fetchHistory]);

  // Handle successful file upload
  const handleUploadSuccess = (jobId) => {
    setSelectedJobId(jobId);
    setJobStatus('pending');
    setJobProgress(0);
    setJobError(null);
    setResults(null);
    setActiveTab('progress');
  };

  // View specific job from history list
  const handleViewJob = async (job) => {
    setSelectedJobId(job.id);
    setJobError(job.error_message);
    setJobStatus(job.status);
    
    if (job.status === 'completed') {
      await fetchResults(job.id);
      setActiveTab('dashboard');
    } else {
      setJobProgress(job.status === 'failed' ? 100 : 50);
      setResults(null);
      setActiveTab('progress');
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'completed') return <CheckCircle className="h-4 w-4 text-emerald-500" />;
    if (status === 'failed') return <XCircle className="h-4 w-4 text-rose-500" />;
    return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
  };

  return (
    <div className="min-h-screen flex flex-col pb-12">
      {/* Premium Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('upload')}>
            <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl shadow-lg shadow-blue-500/20 text-white">
              <Cpu className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <span className="font-extrabold text-lg text-slate-100 tracking-tight">Aero<span className="text-blue-500">Flow</span></span>
              <p className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">Transaction Ingestion Pipeline</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('upload')}
              className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'upload' || activeTab === 'progress'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <PlusCircle className="h-4 w-4" />
              <span>Process CSV</span>
            </button>
            
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <History className="h-4 w-4" />
              <span>Jobs History</span>
            </button>

            {results && (
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                  activeTab === 'dashboard'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <LayoutDashboard className="h-4 w-4" />
                <span>Dashboard</span>
              </button>
            )}
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 mt-8">
        
        {/* TAB 1: FILE UPLOAD */}
        {activeTab === 'upload' && (
          <div className="space-y-8 py-4">
            <div className="text-center space-y-2 max-w-2xl mx-auto">
              <h2 className="text-3xl font-extrabold text-slate-100 tracking-tight">AI-Powered Transaction processing</h2>
              <p className="text-sm text-slate-400">
                Instantly clean dirty spreadsheets, detect outliers, classify merchant spend categories, and generate narrative summaries using Gemini 2.5 Flash.
              </p>
            </div>
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {/* TAB 2: ACTIVE PROGRESS BAR */}
        {activeTab === 'progress' && (
          <div className="py-12 space-y-6">
            <JobProgress progress={jobProgress} status={jobStatus} />
            {jobError && (
              <div className="max-w-xl mx-auto p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start space-x-3 text-red-400">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <div className="text-sm font-medium">
                  <p className="font-semibold">Processing Pipeline Halted</p>
                  <p className="mt-1 font-mono text-xs opacity-90">{jobError}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ANALYTICS DASHBOARD */}
        {activeTab === 'dashboard' && results && (
          <div className="space-y-10 py-2">
            {/* Summary Analytics Cards & AI Narrative */}
            <Dashboard summary={results.summary} />
            
            {/* Full Transaction Records table */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2 text-slate-400">
                <Layers className="h-5 w-5 text-blue-500" />
                <h4 className="font-bold text-slate-200 text-lg">Detailed Transaction Records</h4>
              </div>
              <TransactionTable transactions={results.transactions} />
            </div>
          </div>
        )}

        {/* TAB 4: HISTORICAL JOBS LIST */}
        {activeTab === 'history' && (
          <div className="space-y-6 max-w-4xl mx-auto py-2">
            <div className="flex items-center justify-between pb-2">
              <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <History className="h-5 w-5 text-blue-500" />
                <span>Historical Runs</span>
              </h3>
              <button 
                onClick={fetchHistory}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold cursor-pointer"
              >
                Refresh List
              </button>
            </div>

            {loadingHistory ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-3 text-slate-500">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="text-sm">Querying metadata catalog...</span>
              </div>
            ) : jobsHistory.length === 0 ? (
              <div className="glass-panel p-12 text-center text-slate-500 space-y-4">
                <FileSpreadsheet className="h-12 w-12 mx-auto text-slate-700" />
                <div className="space-y-1">
                  <p className="text-base font-semibold text-slate-400">No previous jobs found</p>
                  <p className="text-xs text-slate-500 max-w-xs mx-auto">Upload a transaction log CSV to begin processing data pipeline.</p>
                </div>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 rounded-xl hover:bg-slate-850 text-xs font-semibold cursor-pointer"
                >
                  Upload First CSV
                </button>
              </div>
            ) : (
              <div className="glass-panel overflow-hidden divide-y divide-slate-850">
                {jobsHistory.map(job => (
                  <div 
                    key={job.id} 
                    onClick={() => handleViewJob(job)}
                    className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-900/40 cursor-pointer transition-all border-l-4 border-transparent hover:border-blue-500"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center space-x-2.5">
                        <span className="font-semibold text-slate-200 text-sm">{job.filename}</span>
                        {getStatusIcon(job.status)}
                      </div>
                      <div className="flex flex-wrap gap-y-1 gap-x-4 text-xs text-slate-400 font-mono">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          <span>{new Date(job.created_at).toLocaleString()}</span>
                        </span>
                        <span>Row Count: {job.row_count_clean}/{job.row_count_raw} (Clean/Raw)</span>
                      </div>
                    </div>

                    <div className="shrink-0 flex items-center space-x-4">
                      {job.status === 'completed' && (
                        <div className="text-right text-xs">
                          <span className="text-slate-400">Total Outflow:</span>
                          <div className="font-bold text-slate-200 font-mono">
                            ₹{job.summary?.total_spend_inr?.toLocaleString() || 0} / ${job.summary?.total_spend_usd?.toLocaleString() || 0}
                          </div>
                        </div>
                      )}
                      
                      <span className="text-xs font-bold text-blue-400 hover:underline uppercase tracking-wide">
                        {job.status === 'completed' ? 'View Results' : 'View Status'} &rarr;
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
