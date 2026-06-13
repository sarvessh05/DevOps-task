import React from 'react';
import { Loader2, Database, ShieldAlert, Cpu, FileJson, CheckCircle } from 'lucide-react';

export default function JobProgress({ progress, status }) {
  // Translate progress numbers to human-readable sub-stages
  const getStageMessage = () => {
    if (status === 'failed') return "Job processing failed.";
    if (progress <= 10) return "Spawning background process thread...";
    if (progress <= 30) return "Deduplicating rows and cleaning date formats...";
    if (progress <= 50) return "Running statistical models to flag anomalies...";
    if (progress <= 80) return "Classifying uncategorized rows via Gemini 2.5 Flash...";
    if (progress <= 95) return "Synthesizing executive narrative & spend patterns...";
    return "Writing clean records to transaction tables...";
  };

  const getStageIcon = () => {
    if (progress <= 10) return <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />;
    if (progress <= 30) return <Database className="h-6 w-6 text-blue-400" />;
    if (progress <= 50) return <ShieldAlert className="h-6 w-6 text-amber-500" />;
    if (progress <= 80) return <Cpu className="h-6 w-6 text-indigo-400 animate-pulse" />;
    if (progress <= 95) return <FileJson className="h-6 w-6 text-purple-400" />;
    return <CheckCircle className="h-6 w-6 text-emerald-500" />;
  };

  return (
    <div className="w-full max-w-xl mx-auto glass-panel p-8 space-y-6 glow-blue">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-slate-950/60 rounded-xl">
            {getStageIcon()}
          </div>
          <div>
            <h4 className="font-semibold text-slate-200">Processing Pipeline</h4>
            <p className="text-xs text-slate-400 font-mono capitalize">Status: {status}</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-blue-500 font-mono">{progress}%</span>
        </div>
      </div>

      <div className="space-y-2">
        {/* Progress Bar Container */}
        <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
          <div
            className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500 transition-all duration-500 ease-out rounded-full shadow-lg shadow-blue-500/50"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {/* Active Stage Label */}
        <div className="flex items-center justify-between text-xs font-medium text-slate-400">
          <span className="animate-pulse">{getStageMessage()}</span>
          <span>{status === 'failed' ? 'Stopped' : 'Processing...'}</span>
        </div>
      </div>
    </div>
  );
}
