import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Flame,
  KeyRound,
  Package,
  FolderGit2,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  HelpCircle,
  X,
  Clock,
  Layers,
  Activity,
  Sparkles,
} from 'lucide-react';
import { CopilotDrawer } from '../components/CopilotDrawer';
import { dashboardService } from '../services/dashboard';
import {
  DashboardSummaryResponse,
  DashboardRepositoriesResponse,
  DashboardFindingsPaginatedResponse,
  DashboardRiskTrendResponse,
  DashboardFindingFilters,
} from '../types';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // State management
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [repositoriesData, setRepositoriesData] = useState<DashboardRepositoriesResponse | null>(null);
  const [findingsData, setFindingsData] = useState<DashboardFindingsPaginatedResponse | null>(null);
  const [, setRiskTrendData] = useState<DashboardRiskTrendResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [findingsLoading, setFindingsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showExplanationModal, setShowExplanationModal] = useState<boolean>(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(false);
  const [copilotInitialPrompt, setCopilotInitialPrompt] = useState<string | null>(null);

  const handleOpenCopilot = (prompt?: string) => {
    setCopilotInitialPrompt(prompt || null);
    setIsCopilotOpen(true);
  };

  // Table filters & pagination
  const [filters, setFilters] = useState<DashboardFindingFilters>({
    page: 1,
    page_size: 10,
    sort_by: 'priority',
  });
  const [searchInput, setSearchInput] = useState<string>('');

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, reposRes, trendRes] = await Promise.all([
        dashboardService.getSummary(),
        dashboardService.getRepositories(),
        dashboardService.getRiskTrend(),
      ]);

      setSummary(sumRes);
      setRepositoriesData(reposRes);
      setRiskTrendData(trendRes);

      // Fetch initial findings page
      const fRes = await dashboardService.getFindings(filters);
      setFindingsData(fRes);
    } catch (err: any) {
      console.error('Failed to load dashboard data', err);
      setError('Unable to load security dashboard. Please verify connection and retry.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchFilteredFindings = useCallback(async (newFilters: DashboardFindingFilters) => {
    setFindingsLoading(true);
    try {
      const fRes = await dashboardService.getFindings(newFilters);
      setFindingsData(fRes);
    } catch (err) {
      console.error('Failed to fetch filtered findings', err);
    } finally {
      setFindingsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Handle Search Input with debounce or submit
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const updated = { ...filters, search: searchInput, page: 1 };
    setFilters(updated);
    fetchFilteredFindings(updated);
  };

  const handleFilterChange = (key: keyof DashboardFindingFilters, value: string) => {
    const updated = { ...filters, [key]: value || undefined, page: 1 };
    setFilters(updated);
    fetchFilteredFindings(updated);
  };

  const handlePageChange = (newPage: number) => {
    const updated = { ...filters, page: newPage };
    setFilters(updated);
    fetchFilteredFindings(updated);
  };

  // Helper formatting functions
  const getScoreRatingColor = (score: number) => {
    if (score >= 90) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 75) return 'text-sky-400 border-sky-500/30 bg-sky-500/10';
    if (score >= 50) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    if (score >= 25) return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
    return 'text-red-400 border-red-500/30 bg-red-500/10';
  };

  const getScoreRatingBadge = (rating: string) => {
    switch (rating?.toLowerCase()) {
      case 'excellent':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
      case 'good':
        return 'bg-sky-500/20 text-sky-300 border-sky-500/30';
      case 'needs attention':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      case 'high risk':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/30';
      default:
        return 'bg-red-500/20 text-red-300 border-red-500/30';
    }
  };

  const getPriorityBadgeClass = (priority?: string) => {
    switch (priority) {
      case 'P0':
        return 'bg-red-500/10 text-red-400 border-red-500/30 font-bold';
      case 'P1':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30 font-semibold';
      case 'P2':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30 font-medium';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const getSeverityBadgeClass = (severity?: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'LOW':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSeconds < 60) return 'Just now';
    const diffMinutes = Math.floor(diffSeconds / 60);
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  // 1. Loading State Skeleton
  if (loading) {
    return (
      <div className="space-y-8 max-w-7xl mx-auto animate-pulse">
        <div className="h-10 bg-slate-900 rounded-lg w-1/3"></div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-56 bg-slate-900 rounded-2xl lg:col-span-2"></div>
          <div className="h-56 bg-slate-900 rounded-2xl"></div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="h-28 bg-slate-900 rounded-xl"></div>
          <div className="h-28 bg-slate-900 rounded-xl"></div>
          <div className="h-28 bg-slate-900 rounded-xl"></div>
          <div className="h-28 bg-slate-900 rounded-xl"></div>
        </div>
        <div className="h-64 bg-slate-900 rounded-xl"></div>
      </div>
    );
  }

  // 2. Error State
  if (error || !summary) {
    return (
      <div className="max-w-xl mx-auto my-16 bg-slate-900 border border-red-500/30 rounded-2xl p-8 text-center space-y-4 shadow-xl">
        <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white">Unable to load security dashboard</h2>
        <p className="text-sm text-slate-400 leading-relaxed">{error || 'An unexpected error occurred while fetching security data.'}</p>
        <button
          onClick={fetchDashboardData}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Retry</span>
        </button>
      </div>
    );
  }

  // 3. Empty State: No Repositories Connected
  if (summary.repositories.total === 0) {
    return (
      <div className="max-w-2xl mx-auto my-12 bg-slate-900 border border-slate-800 rounded-2xl p-10 text-center space-y-6 shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mx-auto shadow-inner">
          <Shield className="w-8 h-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white tracking-tight">Connect your first repository</h2>
          <p className="text-slate-400 text-sm max-w-md mx-auto leading-relaxed">
            Guardrail will scan your codebase for exposed secrets and vulnerable dependencies, giving you clear, prioritized security guidance.
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/repositories/new"
            className="inline-flex items-center space-x-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold px-6 py-3 rounded-xl transition-all shadow-lg hover:shadow-sky-500/20"
          >
            <FolderGit2 className="w-4 h-4" />
            <span>Connect Repository</span>
          </Link>
        </div>
      </div>
    );
  }

  const { findings, types, repositories, scanners, priority_findings, recent_scans, risk_trend, improvements } = summary;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* ── TOP BAR / HEADER ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Security Overview</h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded bg-sky-950/80 text-sky-400 border border-sky-800/40">
              Live
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Welcome back, <span className="text-slate-200 font-medium">{user?.name}</span> — here is your security posture across{' '}
            <span className="text-white font-semibold">{repositories.total}</span> connected {repositories.total === 1 ? 'repository' : 'repositories'}.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleOpenCopilot()}
            className="flex items-center space-x-2 px-3.5 py-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask Copilot</span>
          </button>
          <button
            onClick={fetchDashboardData}
            title="Refresh dashboard metrics"
            className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg border border-slate-800 text-xs font-medium transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <Link
            to="/repositories/new"
            className="flex items-center space-x-2 px-4 py-2 bg-sky-500 hover:bg-sky-400 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-sm"
          >
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Add Repository</span>
          </Link>
        </div>
      </div>

      {/* ── HERO SECTION: SECURITY SCORE + SCANNER HEALTH ───────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Security Score Hero Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-7 flex flex-col justify-between lg:col-span-2 relative overflow-hidden shadow-lg backdrop-blur-sm">
          {/* Subtle gradient glow */}
          <div className="absolute top-0 right-0 w-72 h-72 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Overall Security Score</span>
              <button
                onClick={() => setShowExplanationModal(true)}
                className="text-xs text-sky-400 hover:text-sky-300 flex items-center space-x-1 font-medium transition-colors"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>How is this calculated?</span>
              </button>
            </div>

            <div className="mt-4 flex flex-wrap items-baseline gap-4">
              <div className="flex items-baseline space-x-2">
                <span className="text-5xl sm:text-6xl font-extrabold tracking-tight text-white font-mono">
                  {summary.security_score}
                </span>
                <span className="text-xl text-slate-500 font-medium">/ 100</span>
              </div>

              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${getScoreRatingBadge(summary.rating)}`}>
                {summary.rating} • {summary.risk_level} RISK
              </span>
            </div>

            {/* Score Delta & Comparison */}
            <div className="mt-3 flex items-center space-x-2 text-xs font-medium">
              {summary.score_change !== null && summary.score_change !== undefined ? (
                summary.score_change < 0 ? (
                  <span className="text-red-400 flex items-center space-x-1">
                    <TrendingDown className="w-3.5 h-3.5" />
                    <span>↓ {Math.abs(summary.score_change)} points since previous scan</span>
                  </span>
                ) : summary.score_change > 0 ? (
                  <span className="text-emerald-400 flex items-center space-x-1">
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>↑ {summary.score_change} points improvement</span>
                  </span>
                ) : (
                  <span className="text-slate-400 flex items-center space-x-1">
                    <Minus className="w-3.5 h-3.5" />
                    <span>Score unchanged from previous scan</span>
                  </span>
                )
              ) : (
                <span className="text-slate-500">Baseline score established from current scan</span>
              )}
            </div>

            <p className="text-xs text-slate-400 mt-4 leading-relaxed max-w-xl">
              Your score is based on the severity, exploitability, and exposure of unresolved security findings detected by Guardrail.
            </p>
          </div>

          {/* Quick Delta Improvement Pills */}
          {improvements.new_findings > 0 || improvements.resolved_findings > 0 ? (
            <div className="mt-6 pt-4 border-t border-slate-800/80 flex flex-wrap items-center gap-3 text-xs">
              <span className="text-slate-400 font-medium">Since last scan:</span>
              {improvements.new_findings > 0 && (
                <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-semibold font-mono">
                  +{improvements.new_findings} New
                </span>
              )}
              {improvements.resolved_findings > 0 && (
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold font-mono">
                  -{improvements.resolved_findings} Resolved
                </span>
              )}
              {improvements.persistent_findings > 0 && (
                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50 font-mono">
                  {improvements.persistent_findings} Persistent
                </span>
              )}
            </div>
          ) : null}
        </div>

        {/* Scanner Health & Quick Breakdown Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-lg">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Security Scanners</span>
              <span className="text-[10px] uppercase font-semibold text-slate-500">Engine v1.0</span>
            </div>

            <div className="mt-4 space-y-3">
              {/* Gitleaks Status */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center space-x-3">
                  <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">Gitleaks</div>
                    <div className="text-[11px] text-slate-500">Static secret detection • v8.18.2</div>
                  </div>
                </div>
                <div>
                  {scanners.gitleaks?.operational ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Operational</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                      <XCircle className="w-3 h-3" />
                      <span>Failed</span>
                    </span>
                  )}
                </div>
              </div>

              {/* OSV Status */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="flex items-center space-x-3">
                  <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
                    <Package className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">OSV</div>
                    <div className="text-[11px] text-slate-500">Open-source dependency advisories</div>
                  </div>
                </div>
                <div>
                  {scanners.osv?.operational ? (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Operational</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                      <XCircle className="w-3 h-3" />
                      <span>Failed</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Finding Type Counts summary */}
          <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-2 gap-3 text-center">
            <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60">
              <span className="text-[11px] text-slate-400 font-medium block">Secrets</span>
              <span className="text-lg font-bold text-white font-mono mt-0.5 block">{types.secret}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60">
              <span className="text-[11px] text-slate-400 font-medium block">Dependencies</span>
              <span className="text-lg font-bold text-white font-mono mt-0.5 block">{types.dependency}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── COPILOT QUICK ACTION HERO BANNER ────────────────────────── */}
      <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900/90 to-slate-900 border border-indigo-500/20 rounded-2xl p-5 sm:p-6 shadow-xl relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1 max-w-xl">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-indigo-600/30">
                ✦
              </div>
              <h2 className="text-sm font-bold text-white tracking-wide">Guardrail AI Security Copilot</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                llama3.2:1b Local
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ask contextual questions about your security score, prioritized vulnerabilities, and remediation steps. All facts are strictly grounded in your Phase 4 Risk Engine results.
            </p>
          </div>

          {/* Quick Question Chips */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleOpenCopilot('What should I fix first?')}
              className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 border border-slate-700/60 hover:border-indigo-500/40 text-xs text-slate-200 hover:text-indigo-200 transition flex items-center space-x-1.5"
            >
              <span>🚀</span>
              <span>What should I fix first?</span>
            </button>
            <button
              onClick={() => handleOpenCopilot('Do I have exposed secrets?')}
              className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 border border-slate-700/60 hover:border-indigo-500/40 text-xs text-slate-200 hover:text-indigo-200 transition flex items-center space-x-1.5"
            >
              <span>🔑</span>
              <span>Exposed secrets?</span>
            </button>
            <button
              onClick={() => handleOpenCopilot('Which dependencies are vulnerable?')}
              className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 border border-slate-700/60 hover:border-indigo-500/40 text-xs text-slate-200 hover:text-indigo-200 transition flex items-center space-x-1.5"
            >
              <span>📦</span>
              <span>Vulnerable packages?</span>
            </button>
            <button
              onClick={() => handleOpenCopilot('What changed since my last scan?')}
              className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 border border-slate-700/60 hover:border-indigo-500/40 text-xs text-slate-200 hover:text-indigo-200 transition flex items-center space-x-1.5"
            >
              <span>📊</span>
              <span>Scan diff?</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── METRIC CARDS: SEVERITY COUNTS (CLICKABLE TO FILTER) ─────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Risk Severity Breakdown</h2>
          <span className="text-xs text-slate-500">Click any card to view filtered findings</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Critical */}
          <Link
            to="/findings?status=OPEN&risk_level=CRITICAL"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-red-500/50 hover:bg-slate-850 transition-all flex flex-col justify-between group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Critical</span>
              <Flame className="w-5 h-5 text-red-500 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white font-mono tracking-tight">{findings.critical}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">P0 & P1 immediate threats</div>
            </div>
          </Link>

          {/* High */}
          <Link
            to="/findings?status=OPEN&risk_level=HIGH"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-orange-500/50 hover:bg-slate-850 transition-all flex flex-col justify-between group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">High</span>
              <AlertTriangle className="w-5 h-5 text-orange-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white font-mono tracking-tight">{findings.high}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Urgent remediation items</div>
            </div>
          </Link>

          {/* Medium */}
          <Link
            to="/findings?status=OPEN&risk_level=MEDIUM"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-amber-500/50 hover:bg-slate-850 transition-all flex flex-col justify-between group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Medium</span>
              <ShieldAlert className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white font-mono tracking-tight">{findings.medium}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Important security findings</div>
            </div>
          </Link>

          {/* Low */}
          <Link
            to="/findings?status=OPEN&risk_level=LOW"
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-sky-500/50 hover:bg-slate-850 transition-all flex flex-col justify-between group cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Low</span>
              <ShieldCheck className="w-5 h-5 text-sky-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="mt-4">
              <div className="text-3xl font-bold text-white font-mono tracking-tight">{findings.low}</div>
              <div className="text-xs text-slate-500 mt-1 font-medium">Routine maintenance items</div>
            </div>
          </Link>
        </div>
      </div>

      {/* ── PRIORITY ACTIONS: "FIX THESE FIRST" ─────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span>Fix These First</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Top unresolved findings prioritized by severity, exploitability, and asset risk.</p>
          </div>
          {priority_findings.length > 0 && (
            <Link to="/findings?status=OPEN" className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center space-x-1">
              <span>View all open findings</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {priority_findings.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-white">No active priority risks</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              All scanned repositories currently have zero high-priority findings. New risks will appear here automatically.
            </p>
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-800/80">
              {priority_findings.map((item, idx) => (
                <div
                  key={item.id}
                  className="p-4 sm:p-5 hover:bg-slate-800/30 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="flex items-start space-x-4 min-w-0">
                    <span className="text-xs font-mono text-slate-500 font-bold mt-1 shrink-0">{idx + 1}.</span>

                    {/* Priority Badge */}
                    <span className={`px-2.5 py-1 rounded-md border text-xs font-mono shrink-0 ${getPriorityBadgeClass(item.priority)}`}>
                      {item.priority}
                    </span>

                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getSeverityBadgeClass(item.severity)}`}>
                          {item.severity}
                        </span>
                        <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                          {item.type} • {item.scanner}
                        </span>
                      </div>

                      <div className="text-white font-semibold text-sm truncate" title={item.title}>
                        {item.title}
                      </div>

                      <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
                        <span className="truncate text-slate-300">{item.file_path || 'Repository root'}</span>
                        <span>•</span>
                        <span className="text-slate-500">{item.repository_name}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end space-x-5 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800/60">
                    <div className="text-left sm:text-right">
                      <span className="block text-xs font-bold text-white font-mono">{item.risk_score} / 100</span>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Risk Score</span>
                    </div>

                    <Link
                      to={`/findings/${item.id}`}
                      className="inline-flex items-center space-x-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 px-3.5 py-2 rounded-lg border border-slate-700 transition-colors"
                    >
                      <span>View Finding</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── TWO COLUMN: RISK DISTRIBUTION & RISK TREND ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Visual Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white mb-1">Risk Distribution</h3>
            <p className="text-xs text-slate-400">Distribution of all active open findings by severity.</p>

            <div className="mt-6 space-y-4">
              {/* Critical Bar */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-red-400">Critical</span>
                  <span className="text-white font-mono">{findings.critical}</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${findings.open > 0 ? (findings.critical / findings.open) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* High Bar */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-orange-400">High</span>
                  <span className="text-white font-mono">{findings.high}</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-400 rounded-full transition-all duration-500"
                    style={{
                      width: `${findings.open > 0 ? (findings.high / findings.open) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* Medium Bar */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-amber-400">Medium</span>
                  <span className="text-white font-mono">{findings.medium}</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-amber-400 rounded-full transition-all duration-500"
                    style={{
                      width: `${findings.open > 0 ? (findings.medium / findings.open) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>

              {/* Low Bar */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-sky-400">Low</span>
                  <span className="text-white font-mono">{findings.low}</span>
                </div>
                <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-sky-400 rounded-full transition-all duration-500"
                    style={{
                      width: `${findings.open > 0 ? (findings.low / findings.open) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 text-xs text-slate-500 flex justify-between">
            <span>Total Open Findings: <strong className="text-slate-200">{findings.open}</strong></span>
            <span>Resolved Findings: <strong className="text-slate-200">{findings.resolved}</strong></span>
          </div>
        </div>

        {/* Risk Trend Timeline Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Security Score Trend</h3>
              <span className="text-[11px] text-slate-500 font-medium">Historical Scans</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Historical progression of your security score over time.</p>

            {/* If fewer than 2 scans exist, display clean prompt without fabricating data */}
            {risk_trend.length < 2 ? (
              <div className="my-8 py-8 px-4 bg-slate-950/60 border border-slate-800/80 rounded-xl text-center space-y-2">
                <Activity className="w-8 h-8 text-slate-600 mx-auto" />
                <h4 className="text-sm font-semibold text-slate-300">Not enough scan history yet</h4>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  Historical security trends will automatically render here as you run multiple scans over time.
                </p>
              </div>
            ) : (
              <div className="mt-6 space-y-3">
                <div className="space-y-2">
                  {risk_trend.slice(-5).map((point, i) => (
                    <div
                      key={point.scan_id || i}
                      className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center font-mono text-[10px] text-slate-400 font-bold">
                          {i + 1}
                        </span>
                        <div>
                          <div className="font-medium text-slate-200">{point.repository_name}</div>
                          <div className="text-[10px] text-slate-500">{point.date}</div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        <span className="text-slate-400 font-mono">{point.finding_count} findings</span>
                        <span className={`px-2 py-0.5 rounded font-mono font-bold border text-xs ${getScoreRatingColor(point.security_score)}`}>
                          {point.security_score} / 100
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-slate-500 flex justify-between items-center">
            <span>Total Completed Scans: <strong className="text-slate-200">{risk_trend.length}</strong></span>
            {risk_trend.length >= 2 && (
              <span className="text-sky-400 font-medium">Actual scan metrics recorded</span>
            )}
          </div>
        </div>
      </div>

      {/* ── CONNECTED REPOSITORIES SECTION ──────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <FolderGit2 className="w-5 h-5 text-sky-400" />
              <span>Repositories</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Overview and individual security ratings of all connected repositories.</p>
          </div>
          <Link to="/repositories" className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center space-x-1">
            <span>Manage repositories</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {repositoriesData && repositoriesData.repositories.length > 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-4">Repository</th>
                    <th className="p-4">Language</th>
                    <th className="p-4">Security Score</th>
                    <th className="p-4">Finding Breakdown</th>
                    <th className="p-4">Last Scan</th>
                    <th className="p-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 text-slate-300 font-medium">
                  {repositoriesData.repositories.map((repo) => (
                    <tr key={repo.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4">
                        <Link to={`/repositories/${repo.id}`} className="font-semibold text-white hover:text-sky-400 transition-colors">
                          {repo.name}
                        </Link>
                        <div className="text-[11px] text-slate-500 font-mono mt-0.5">{repo.default_branch}</div>
                      </td>

                      <td className="p-4">
                        <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700/60 text-xs font-semibold">
                          {repo.primary_language || 'General'}
                        </span>
                      </td>

                      <td className="p-4">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2.5 py-1 rounded-md border font-mono font-bold text-xs ${getScoreRatingColor(repo.security_score)}`}>
                            {repo.security_score} / 100
                          </span>
                          <span className="text-[11px] text-slate-400 font-medium">{repo.rating}</span>
                        </div>
                      </td>

                      <td className="p-4">
                        <div className="flex items-center space-x-2 font-mono text-[11px]">
                          {repo.finding_counts.critical > 0 && (
                            <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-bold">
                              {repo.finding_counts.critical} Crit
                            </span>
                          )}
                          {repo.finding_counts.high > 0 && (
                            <span className="px-2 py-0.5 rounded bg-orange-500/10 text-orange-400 border border-orange-500/20 font-semibold">
                              {repo.finding_counts.high} High
                            </span>
                          )}
                          {repo.finding_counts.medium > 0 && (
                            <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              {repo.finding_counts.medium} Med
                            </span>
                          )}
                          {repo.finding_counts.low > 0 && (
                            <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">
                              {repo.finding_counts.low} Low
                            </span>
                          )}
                          {repo.finding_counts.total_open === 0 && (
                            <span className="text-emerald-400 font-sans font-semibold">Clean (0 issues)</span>
                          )}
                        </div>
                      </td>

                      <td className="p-4 text-slate-400">
                        <div>{formatRelativeTime(repo.last_scan_at)}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5 font-medium uppercase">{repo.last_scan_status || 'Unscanned'}</div>
                      </td>

                      <td className="p-4 text-right">
                        <Link
                          to={`/repositories/${repo.id}`}
                          className="inline-flex items-center space-x-1 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors"
                        >
                          <span>View Repo</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </div>

      {/* ── RECENT SCAN ACTIVITY ────────────────────────────────────── */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Clock className="w-5 h-5 text-indigo-400" />
            <span>Recent Scan Activity</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Audit log of recent automated security scans across your repositories.</p>
        </div>

        {recent_scans.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center text-xs text-slate-500">
            No scan history recorded yet. Trigger a scan from any connected repository.
          </div>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-4">Repository</th>
                    <th className="p-4">Scan Started</th>
                    <th className="p-4">Duration</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Findings</th>
                    <th className="p-4">Scanner Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 text-slate-300 font-medium">
                  {recent_scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4 font-semibold text-white">
                        <Link to={`/repositories/${scan.repository_id}`} className="hover:text-sky-400">
                          {scan.repository_name}
                        </Link>
                      </td>
                      <td className="p-4 text-slate-400">
                        {scan.started_at ? new Date(scan.started_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-4 font-mono text-slate-400">
                        {scan.duration_seconds !== null && scan.duration_seconds !== undefined
                          ? `${scan.duration_seconds}s`
                          : 'N/A'}
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                            scan.status === 'COMPLETED'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : scan.status === 'RUNNING'
                              ? 'bg-sky-500/10 text-sky-400 border-sky-500/20'
                              : 'bg-red-500/10 text-red-400 border-red-500/20'
                          }`}
                        >
                          {scan.status}
                        </span>
                      </td>
                      <td className="p-4 font-mono font-semibold text-white">{scan.total_findings}</td>
                      <td className="p-4">
                        <div className="flex items-center space-x-3">
                          <span className="flex items-center space-x-1 text-[11px] text-slate-300">
                            <span>Gitleaks</span>
                            {scan.scanners?.gitleaks?.status === 'FAILED' ? (
                              <XCircle className="w-3.5 h-3.5 text-red-400" />
                            ) : (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            )}
                          </span>
                          <span className="flex items-center space-x-1 text-[11px] text-slate-300">
                            <span>OSV</span>
                            {scan.scanners?.osv?.status === 'FAILED' ? (
                              <XCircle className="w-3.5 h-3.5 text-red-400" />
                            ) : (
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                            )}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ── ALL FINDINGS FEED WITH SEARCH & FILTERS ─────────────────── */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-sky-400" />
              <span>Recent Security Findings</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Filterable inventory of security detections across your repositories.</p>
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search findings, packages, files..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </form>
        </div>

        {/* Filter Controls Row */}
        <div className="flex flex-wrap items-center gap-3 p-3 bg-slate-900/60 border border-slate-800/80 rounded-xl text-xs">
          <div className="flex items-center space-x-1 text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span className="font-semibold uppercase tracking-wider text-[10px]">Filter:</span>
          </div>

          {/* Severity filter */}
          <select
            value={filters.severity || ''}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Type filter */}
          <select
            value={filters.type || ''}
            onChange={(e) => handleFilterChange('type', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Types</option>
            <option value="SECRET">Secrets</option>
            <option value="DEPENDENCY">Dependencies</option>
          </select>

          {/* Status filter */}
          <select
            value={filters.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open Only</option>
            <option value="RESOLVED">Resolved Only</option>
          </select>

          {/* Scanner filter */}
          <select
            value={filters.scanner || ''}
            onChange={(e) => handleFilterChange('scanner', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            <option value="">All Scanners</option>
            <option value="gitleaks">Gitleaks</option>
            <option value="osv">OSV</option>
          </select>

          {/* Sort By */}
          <select
            value={filters.sort_by || 'priority'}
            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 ml-auto"
          >
            <option value="priority">Sort: Priority (P0→P3)</option>
            <option value="risk_score">Sort: Risk Score (High→Low)</option>
            <option value="severity">Sort: Severity</option>
            <option value="created_at">Sort: Newest First</option>
          </select>
        </div>

        {/* Findings Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          {findingsLoading ? (
            <div className="flex items-center justify-center p-12">
              <RefreshCw className="w-6 h-6 text-sky-500 animate-spin" />
            </div>
          ) : !findingsData || findingsData.findings.length === 0 ? (
            <div className="p-10 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
              <h3 className="text-sm font-semibold text-slate-300">No matching security findings</h3>
              <p className="text-xs text-slate-500">Try adjusting your filters or search terms.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-4">Severity</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Finding</th>
                    <th className="p-4">Repository</th>
                    <th className="p-4">Location</th>
                    <th className="p-4">Scanner</th>
                    <th className="p-4">Risk Score</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80 text-slate-300 font-medium">
                  {findingsData.findings.map((f) => (
                    <tr
                      key={f.id}
                      onClick={() => navigate(`/findings/${f.id}`)}
                      className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                    >
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${getSeverityBadgeClass(f.severity)}`}>
                          {f.severity}
                        </span>
                      </td>

                      <td className="p-4">
                        <span className="font-semibold text-[11px] text-slate-300 uppercase">{f.type}</span>
                      </td>

                      <td className="p-4 font-semibold text-white max-w-xs truncate" title={f.title}>
                        {f.title}
                      </td>

                      <td className="p-4 text-slate-400">{f.repository_name}</td>

                      <td className="p-4 font-mono text-[11px] text-slate-400 truncate max-w-xs">
                        {f.file_path || 'Repository root'}
                      </td>

                      <td className="p-4 text-slate-400 capitalize">{f.scanner}</td>

                      <td className="p-4">
                        <span className="font-mono font-bold text-white">{f.risk_score}</span>
                        <span className="text-[10px] text-slate-500 ml-1 font-semibold">{f.priority}</span>
                      </td>

                      <td className="p-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            f.status === 'OPEN'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          }`}
                        >
                          {f.status}
                        </span>
                      </td>

                      <td className="p-4 text-right">
                        <Link
                          to={`/findings/${f.id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-sky-400 hover:text-sky-300 font-semibold"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {findingsData && findingsData.total_pages > 1 && (
            <div className="p-4 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs">
              <span className="text-slate-400">
                Showing page <strong className="text-white">{findingsData.page}</strong> of{' '}
                <strong className="text-white">{findingsData.total_pages}</strong> ({findingsData.total} total findings)
              </span>

              <div className="flex items-center space-x-2">
                <button
                  disabled={findingsData.page <= 1}
                  onClick={() => handlePageChange(findingsData.page - 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  disabled={findingsData.page >= findingsData.total_pages}
                  onClick={() => handlePageChange(findingsData.page + 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── MODAL: HOW IS THE SECURITY SCORE CALCULATED? ─────────────── */}
      {showExplanationModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 sm:p-7 space-y-6 shadow-2xl relative">
            <button
              onClick={() => setShowExplanationModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">How is the Security Score calculated?</h3>
                <p className="text-xs text-slate-400">Powered by the Guardrail Risk Engine</p>
              </div>
            </div>

            <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
              <p>
                Your overall Security Score starts at <strong className="text-emerald-400">100 / 100</strong> (Clean) and decreases based on the risk impact of active unresolved security findings detected across your repositories.
              </p>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="font-semibold text-white text-[11px] uppercase tracking-wider">Score Classifications:</div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div><span className="text-emerald-400 font-bold">90–100:</span> Excellent</div>
                  <div><span className="text-sky-400 font-bold">75–89:</span> Good</div>
                  <div><span className="text-amber-400 font-bold">50–74:</span> Needs Attention</div>
                  <div><span className="text-orange-400 font-bold">25–49:</span> High Risk</div>
                  <div className="col-span-2"><span className="text-red-400 font-bold">0–24:</span> Critical Risk</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="font-semibold text-white text-[11px] uppercase tracking-wider">Evaluation Factors:</div>
                <ul className="space-y-1.5 list-disc list-inside text-slate-400">
                  <li><strong className="text-slate-200">Severity Baseline:</strong> Base impact of the vulnerability or secret.</li>
                  <li><strong className="text-slate-200">Exploitability:</strong> How easily the vulnerability can be leveraged.</li>
                  <li><strong className="text-slate-200">Exposure:</strong> Public vs internal repository accessibility.</li>
                  <li><strong className="text-slate-200">Asset Criticality:</strong> Importance of the impacted repository.</li>
                  <li><strong className="text-slate-200">Scanner Confidence:</strong> Verified scanner certainty.</li>
                </ul>
              </div>

              <div className="p-3 rounded-lg bg-sky-950/30 border border-sky-800/40 text-sky-300 text-[11px]">
                Note: A high score indicates that enabled scanners detected few or no active issues, but continuous scanning is recommended as new threats emerge.
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowExplanationModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold transition-colors"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Copilot Drawer */}
      <CopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => {
          setIsCopilotOpen(false);
          setCopilotInitialPrompt(null);
        }}
        initialPrompt={copilotInitialPrompt}
      />
    </div>
  );
};

export default DashboardPage;
