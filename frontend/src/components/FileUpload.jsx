import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, Loader2 } from 'lucide-react';

export default function FileUpload({ onUploadSuccess }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const processFile = async (file) => {
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setError("Unsupported file format. Please upload a valid CSV file (.csv).");
      return;
    }

    setError(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/jobs/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errDetail = await response.json();
        throw new Error(errDetail?.detail || "Upload failed");
      }

      const data = await response.json();
      onUploadSuccess(data.job_id);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to upload file. Please check if backend is running.");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`glass-panel p-8 text-center border-2 border-dashed transition-all duration-300 ${
          isDragActive 
            ? 'border-blue-500 bg-blue-500/5' 
            : 'border-slate-800 hover:border-slate-700 bg-slate-900/40'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
          disabled={uploading}
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="p-4 bg-slate-950/60 rounded-full text-blue-500 ring-4 ring-slate-900/60">
            {uploading ? (
              <Loader2 className="h-10 w-10 animate-spin" />
            ) : (
              <Upload className="h-10 w-10" />
            )}
          </div>

          <div className="space-y-1">
            <h3 className="text-lg font-semibold text-slate-200">
              {uploading ? "Ingesting Transaction Log..." : "Upload your financial transactions"}
            </h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">
              Drag and drop your <span className="font-medium text-slate-300">transactions.csv</span> here, or click to browse local files.
            </p>
          </div>

          {!uploading && (
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/20 transition-all duration-200"
            >
              Select File
            </button>
          )}

          {uploading && (
            <div className="flex items-center space-x-2 text-sm text-blue-400 font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              <span>Spawning worker thread...</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start space-x-3 text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}
    </div>
  );
}
