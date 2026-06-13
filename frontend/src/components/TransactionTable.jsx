import React, { useState } from 'react';
import { Search, AlertTriangle, Cpu, Check, X, ShieldAlert, Sparkles, Filter } from 'lucide-react';

export default function TransactionTable({ transactions }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [currencyFilter, setCurrencyFilter] = useState('ALL');
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);

  // Extract unique categories
  const categories = ['ALL', ...new Set(transactions.map(t => t.category.toUpperCase()))];
  const currencies = ['ALL', ...new Set(transactions.map(t => t.currency.toUpperCase()))];

  const filteredTransactions = transactions.filter(t => {
    const matchesSearch = 
      t.merchant.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.account_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (t.txn_id && t.txn_id.toLowerCase().includes(searchTerm.toLowerCase()));
      
    const matchesCategory = categoryFilter === 'ALL' || t.category.toUpperCase() === categoryFilter;
    const matchesCurrency = currencyFilter === 'ALL' || t.currency.toUpperCase() === currencyFilter;
    const matchesAnomaly = !showAnomaliesOnly || t.is_anomaly;

    return matchesSearch && matchesCategory && matchesCurrency && matchesAnomaly;
  });

  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Check className="h-3.5 w-3.5" />
            <span>Success</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <X className="h-3.5 w-3.5" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            <span>Pending</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Filtering Row */}
      <div className="glass-panel p-6 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search merchant, account..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 rounded-xl text-sm text-slate-200 outline-none transition-all"
          />
        </div>

        {/* Category Filter */}
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-slate-500 shrink-0" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 cursor-pointer"
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        {/* Currency Filter */}
        <div className="flex items-center space-x-2">
          <select
            value={currencyFilter}
            onChange={(e) => setCurrencyFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 text-slate-300 rounded-xl px-3 py-2 text-sm outline-none focus:border-blue-500 cursor-pointer"
          >
            <option value="ALL">All Currencies</option>
            {currencies.map(curr => (
              <option key={curr} value={curr}>{curr}</option>
            ))}
          </select>
        </div>

        {/* Anomalies Only Toggle */}
        <div className="flex items-center justify-end">
          <label className="flex items-center space-x-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showAnomaliesOnly}
              onChange={(e) => setShowAnomaliesOnly(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-850 rounded-full peer peer-focus:ring-1 peer-focus:ring-blue-500 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-checked:after:bg-white relative"></div>
            <span className="text-sm font-medium text-slate-300 flex items-center gap-1.5">
              <ShieldAlert className={`h-4 w-4 ${showAnomaliesOnly ? 'text-rose-400' : 'text-slate-400'}`} />
              <span>Anomalies Only</span>
            </span>
          </label>
        </div>
      </div>

      {/* Table Container */}
      <div className="glass-panel overflow-hidden border border-slate-800/80">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold text-xs tracking-wider uppercase">
                <th className="px-6 py-4">Txn ID</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Merchant</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Account ID</th>
                <th className="px-6 py-4">Analysis / Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-slate-500 text-sm">
                    No transactions found matching your active filter criteria.
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((txn, index) => (
                  <tr 
                    key={txn.id || index}
                    className={`transition-colors text-sm ${
                      txn.is_anomaly 
                        ? 'bg-rose-500/5 hover:bg-rose-500/10' 
                        : 'hover:bg-slate-900/40'
                    }`}
                  >
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">
                      {txn.txn_id || <span className="text-slate-600 italic">Missing</span>}
                    </td>
                    <td className="px-6 py-4 text-slate-300">
                      {txn.date || <span className="text-slate-600 italic">Null</span>}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-200">
                      {txn.merchant}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-200">
                      {txn.currency === 'INR' ? '₹' : '$'}
                      {txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-slate-200">{txn.category}</span>
                        {txn.llm_category && (
                          <div className="text-indigo-400" title="Classified by Gemini AI">
                            <Sparkles className="h-3.5 w-3.5" />
                          </div>
                        )}
                        {txn.llm_failed && (
                          <span className="text-[10px] px-1 bg-red-950 text-red-400 rounded border border-red-500/10">
                            AI Failed
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(txn.status)}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-300">
                      {txn.account_id}
                    </td>
                    <td className="px-6 py-4">
                      {txn.is_anomaly ? (
                        <div className="flex items-start gap-1.5 text-rose-400 text-xs bg-rose-500/10 p-2 rounded-lg border border-rose-500/20 max-w-xs">
                          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                          <span>{txn.anomaly_reason}</span>
                        </div>
                      ) : txn.notes ? (
                        <span className="text-xs text-slate-400 italic max-w-xs inline-block truncate" title={txn.notes}>
                          {txn.notes}
                        </span>
                      ) : (
                        <span className="text-slate-600 italic text-xs">-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
