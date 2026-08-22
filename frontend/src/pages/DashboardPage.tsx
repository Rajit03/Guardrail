import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AlertTriangle, ShieldCheck, Inbox, Flame, ShieldAlert, ArrowRight } from 'lucide-react';
import { findingService } from '../services/scan';
import { Finding } from '../types';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [criticalRiskCount, setCriticalRiskCount] = useState<number>(0);
  const [highRiskCount, setHighRiskCount] = useState<number>(0);
  const [mediumRiskCount, setMediumRiskCount] = useState<number>(0);
  const [lowRiskCount, setLowRiskCount] = useState<number>(0);
  const [topRisks, setTopRisks] = useState<Finding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const openFindings = await findingService.getFindings({ status: 'OPEN', sort_by: 'priority' });

        let critical = 0;
        let high = 0;
        let medium = 0;
        let low = 0;

        openFindings.forEach((f) => {
          const level = f.risk_level || 'INFO';
          if (level === 'CRITICAL') critical++;
          else if (level === 'HIGH') high++;
          else if (level === 'MEDIUM') medium++;
          else if (level === 'LOW') low++;
        });

        setCriticalRiskCount(critical);
        setHighRiskCount(high);
        setMediumRiskCount(medium);
        setLowRiskCount(low);

        // Top 5 highest risk open findings
        setTopRisks(openFindings.slice(0, 5));
      } catch (error) {
        console.error('Failed to fetch dashboard metrics', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getPriorityBadgeClass = (priority?: string) => {
    switch (priority) {
      case 'P0': return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'P1': return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'P2': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Guardrail
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Welcome, <span className="text-slate-200 font-semibold">{user?.name}</span>
          </p>
        </div>
      </div>

      {/* Risk Overview Header */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Risk Overview</h2>
        <p className="text-xs text-slate-400">Prioritized security risk breakdown across your connected assets.</p>
      </div>

      {/* Risk Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link to="/findings?status=OPEN&risk_level=CRITICAL" className="block cursor-pointer">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-red-500/40 transition-all flex flex-col justify-between h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Critical Risks</span>
              <Flame className="w-5 h-5 text-red-500" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white tracking-tight">{criticalRiskCount}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">P0 & P1 immediate threats</div>
            </div>
          </div>
        </Link>

        <Link to="/findings?status=OPEN&risk_level=HIGH" className="block cursor-pointer">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-orange-500/40 transition-all flex flex-col justify-between h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">High Risks</span>
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white tracking-tight">{highRiskCount}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Urgent remediation items</div>
            </div>
          </div>
        </Link>

        <Link to="/findings?status=OPEN&risk_level=MEDIUM" className="block cursor-pointer">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-amber-500/40 transition-all flex flex-col justify-between h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Medium Risks</span>
              <ShieldAlert className="w-5 h-5 text-amber-400" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white tracking-tight">{mediumRiskCount}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Important security findings</div>
            </div>
          </div>
        </Link>

        <Link to="/findings?status=OPEN&risk_level=LOW" className="block cursor-pointer">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-sky-500/40 transition-all flex flex-col justify-between h-full">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Low Risks</span>
              <ShieldCheck className="w-5 h-5 text-sky-400" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white tracking-tight">{lowRiskCount}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Routine maintenance items</div>
            </div>
          </div>
        </Link>
      </div>

      {/* Top Risks Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Top Priority Risks</h2>
          {topRisks.length > 0 && (
            <Link to="/findings" className="text-xs font-medium text-sky-400 hover:text-sky-300 flex items-center space-x-1">
              <span>View all findings</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500"></div>
          </div>
        ) : topRisks.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center flex flex-col items-center justify-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-500 shadow-inner">
              <Inbox className="w-7 h-7 text-sky-500/80" />
            </div>
            <div className="space-y-1.5 max-w-md">
              <h2 className="text-lg font-semibold text-slate-200">
                No active risks detected.
              </h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                Your security insights will appear here once you scan a repository.
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-800/80">
              {topRisks.map((finding) => (
                <div key={finding.id} className="p-4 hover:bg-slate-800/30 transition-colors flex items-center justify-between gap-4">
                  <div className="flex items-center space-x-4 min-w-0">
                    <span className={`px-2.5 py-1 rounded-md border text-xs font-mono font-bold ${getPriorityBadgeClass(finding.priority)}`}>
                      {finding.priority || 'P3'}
                    </span>
                    <div className="min-w-0">
                      <div className="text-white font-medium text-sm truncate" title={finding.title}>
                        {finding.title}
                      </div>
                      <div className="text-xs text-slate-500 font-mono mt-0.5 truncate">
                        {finding.file_path || 'Repository root'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-6 shrink-0 text-right">
                    <div>
                      <span className="block text-xs font-semibold text-white">{finding.risk_score ?? 0} / 100</span>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">{finding.risk_level || 'INFO'}</span>
                    </div>
                    <Link
                      to={`/findings/${finding.id}`}
                      className="text-xs font-medium bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors"
                    >
                      View Risk →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
