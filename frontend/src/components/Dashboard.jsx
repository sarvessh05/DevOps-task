import React from 'react';
import { 
  TrendingUp, 
  DollarSign, 
  ShieldAlert, 
  Activity, 
  Zap,
  Award,
  ListFilter
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';

export default function Dashboard({ summary }) {
  if (!summary) return null;

  const {
    total_spend_inr,
    total_spend_usd,
    top_merchants,
    category_breakdown,
    anomaly_count,
    narrative,
    risk_level
  } = summary;

  // Format category breakdown data for Recharts double-bar chart
  const categoryData = Object.entries(category_breakdown).map(([name, spend]) => ({
    name,
    INR: parseFloat(spend.INR.toFixed(2)),
    USD: parseFloat(spend.USD.toFixed(2))
  }));

  // Format merchant data
  const merchantData = top_merchants.map(item => ({
    name: item.merchant,
    INR: item.spend_inr,
    USD: item.spend_usd
  }));

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'text-red-400 border-red-500/20 bg-red-500/10 glow-red';
      case 'medium':
        return 'text-amber-400 border-amber-500/20 bg-amber-500/10';
      default:
        return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Metric: Total INR */}
        <div className="glass-panel p-6 glass-panel-hover flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium tracking-wider uppercase">Total INR Outflow</span>
            <h3 className="text-2xl font-extrabold text-slate-100">₹{total_spend_inr.toLocaleString('en-IN')}</h3>
          </div>
          <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
            <TrendingUp className="h-6 w-6" />
          </div>
        </div>

        {/* Metric: Total USD */}
        <div className="glass-panel p-6 glass-panel-hover flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium tracking-wider uppercase">Total USD Outflow</span>
            <h3 className="text-2xl font-extrabold text-slate-100">${total_spend_usd.toLocaleString('en-US')}</h3>
          </div>
          <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-500">
            <DollarSign className="h-6 w-6" />
          </div>
        </div>

        {/* Metric: Anomalies */}
        <div className="glass-panel p-6 glass-panel-hover flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-xs text-slate-400 font-medium tracking-wider uppercase">Flagged Outliers</span>
            <h3 className={`text-2xl font-extrabold ${anomaly_count > 0 ? 'text-rose-400' : 'text-slate-100'}`}>
              {anomaly_count}
            </h3>
          </div>
          <div className={`p-3 rounded-xl ${anomaly_count > 0 ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-800 text-slate-400'}`}>
            <ShieldAlert className="h-6 w-6" />
          </div>
        </div>

        {/* Metric: Risk Level */}
        <div className={`glass-panel p-6 border flex items-center justify-between ${getRiskColor(risk_level)}`}>
          <div className="space-y-1">
            <span className="text-xs text-slate-300 font-medium tracking-wider uppercase">Risk Evaluation</span>
            <h3 className="text-2xl font-extrabold uppercase tracking-wide">{risk_level || 'UNKNOWN'}</h3>
          </div>
          <div className="p-3 bg-slate-950/40 rounded-xl">
            <Activity className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* AI Narrative Section */}
      <div className="glass-panel p-8 relative overflow-hidden bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-blue-950/20 border border-slate-800 glow-blue">
        <div className="absolute top-0 right-0 -mt-4 -mr-4 p-8 bg-blue-500/10 rounded-full blur-2xl"></div>
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex items-center space-x-2 text-blue-400 font-semibold text-sm">
              <Zap className="h-4 w-4" />
              <span>AI Executive Narrative Summary</span>
            </div>
            <p className="text-slate-300 text-base leading-relaxed italic">
              "{narrative}"
            </p>
          </div>
          <div className="shrink-0 flex items-center space-x-2 text-slate-400 text-xs font-mono bg-slate-950/60 px-4 py-2 rounded-xl border border-slate-800">
            <Award className="h-4 w-4 text-amber-500" />
            <span>Gemini 2.5 Flash Verified</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Category breakdown double bar chart */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="font-semibold text-slate-200 flex items-center gap-2">
              <ListFilter className="h-4 w-4 text-blue-500" />
              <span>Expenditure by Category</span>
            </h4>
            <span className="text-xs text-slate-400">INR / USD Breakdown</span>
          </div>
          
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={categoryData}
                margin={{ top: 20, right: 10, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis yAxisId="left" stroke="#3b82f6" fontSize={11} label={{ value: 'INR (₹)', angle: -90, position: 'insideLeft', style: { fill: '#3b82f6', fontSize: 10 } }} tickLine={false} />
                <YAxis yAxisId="right" orientation="right" stroke="#10b981" fontSize={11} label={{ value: 'USD ($)', angle: 90, position: 'insideRight', style: { fill: '#10b981', fontSize: 10 } }} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  labelStyle={{ fontWeight: 'bold', color: '#cbd5e1' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                <Bar yAxisId="left" dataKey="INR" fill="#3b82f6" radius={[4, 4, 0, 0]} name="INR spend (₹)" />
                <Bar yAxisId="right" dataKey="USD" fill="#10b981" radius={[4, 4, 0, 0]} name="USD spend ($)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Merchants spend chart */}
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="font-semibold text-slate-200 flex items-center gap-2">
              <Award className="h-4 w-4 text-emerald-500" />
              <span>Top Merchants spend</span>
            </h4>
            <span className="text-xs text-slate-400">Total volume</span>
          </div>

          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={merchantData}
                layout="vertical"
                margin={{ top: 20, right: 10, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={true} vertical={false} />
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  labelStyle={{ fontWeight: 'bold', color: '#cbd5e1' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="INR" fill="#2563eb" radius={[0, 4, 4, 0]} name="Spend INR (₹)" stackId="a" />
                <Bar dataKey="USD" fill="#059669" radius={[0, 4, 4, 0]} name="Spend USD ($)" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
