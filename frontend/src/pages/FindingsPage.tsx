import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ShieldAlert, Filter, RefreshCw, FolderGit2, ArrowUpDown, Package, KeyRound } from 'lucide-react';
import { findingService, scanService } from '../services/scan';
import { repositoryService } from '../services/repository';
import { Finding, Repository, FindingFilters } from '../types';

export const FindingsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [findings, setFindings] = useState<Finding[]>([]);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  // Read filters from URL params
  const repositoryId = searchParams.get('repository_id') || '';
  const severity = searchParams.get('severity') || '';
  const type = searchParams.get('type') || '';
  const status = searchParams.get('status') || '';
  const riskLevel = searchParams.get('risk_level') || '';
  const priority = searchParams.get('priority') || '';
  const sortBy = searchParams.get('sort_by') || 'priority';
  const scanId = searchParams.get('scan_id') || '';

  useEffect(() => {
    const fetchFiltersData = async () => {
      try {
        const repos = await repositoryService.getRepositories();
        setRepositories(repos);
      } catch (error) {
        console.error('Failed to fetch repositories for filter', error);
      }
    };
    fetchFiltersData();
  }, []);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      let data: Finding[] = [];
      if (scanId) {
        data = await scanService.getScanFindings(scanId);
      } else {
        const filters: FindingFilters = {};
        if (repositoryId) filters.repository_id = repositoryId;
        if (severity) filters.severity = severity;
        if (type) filters.type = type;
        if (status) filters.status = status;
        if (riskLevel) filters.risk_level = riskLevel;
        if (priority) filters.priority = priority;
        if (sortBy) filters.sort_by = sortBy;
        data = await findingService.getFindings(filters);
      }
      setFindings(data);
    } catch (error) {
      console.error('Failed to fetch findings', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, [repositoryId, severity, type, status, riskLevel, priority, sortBy, scanId]);

  const handleFilterChange = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    if (key !== 'scan_id') {
      newParams.delete('scan_id');
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const getPriorityBadgeClass = (p?: string) => {
    switch (p) {
      case 'P0': return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'P1': return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'P2': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const getRiskLevelBadgeClass = (level?: string) => {
    switch (level) {
      case 'CRITICAL': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'HIGH': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MEDIUM': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LOW': return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-sky-400" />
            <span>Security Findings</span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            {scanId ? 'Findings detected in this scan.' : 'Prioritized vulnerabilities and secrets detected across your repositories.'}
          </p>
        </div>
        <button
          onClick={fetchFindings}
          className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white px-3.5 py-2 rounded-lg text-sm font-medium border border-slate-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Bar */}
      {!scanId && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap gap-3 items-center">
          <div className="flex items-center space-x-2 text-slate-400 text-sm">
            <Filter className="w-4 h-4" />
            <span>Filters:</span>
          </div>

          {/* Priority Filter */}
          <select
            value={priority}
            onChange={(e) => handleFilterChange('priority', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Priorities</option>
            <option value="P0">P0 — Immediate</option>
            <option value="P1">P1 — Urgent</option>
            <option value="P2">P2 — Important</option>
            <option value="P3">P3 — Routine</option>
          </select>

          {/* Risk Level Filter */}
          <select
            value={riskLevel}
            onChange={(e) => handleFilterChange('risk_level', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Risk Levels</option>
            <option value="CRITICAL">Critical Risk</option>
            <option value="HIGH">High Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="LOW">Low Risk</option>
            <option value="INFO">Info</option>
          </select>

          {/* Repository Filter */}
          <select
            value={repositoryId}
            onChange={(e) => handleFilterChange('repository_id', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Repositories</option>
            {repositories.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name}
              </option>
            ))}
          </select>

          {/* Type Filter */}
          <select
            value={type}
            onChange={(e) => handleFilterChange('type', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Types</option>
            <option value="SECRET">Secret</option>
            <option value="DEPENDENCY">Dependency</option>
          </select>

          {/* Status Filter */}
          <select
            value={status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>

          {/* Sort By */}
          <div className="flex items-center space-x-1.5 ml-auto border-l border-slate-800 pl-3">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={sortBy}
              onChange={(e) => handleFilterChange('sort_by', e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
            >
              <option value="priority">Sort by Priority (P0 → P3)</option>
              <option value="risk_score">Sort by Risk Score (Desc)</option>
              <option value="severity">Sort by Severity</option>
              <option value="created_at">Sort by Date Detected</option>
            </select>
          </div>

          {(repositoryId || severity || type || status || riskLevel || priority) && (
            <button
              onClick={clearFilters}
              className="text-xs text-sky-400 hover:text-sky-300 font-medium"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {scanId && (
        <div className="bg-sky-950/40 border border-sky-900/60 rounded-xl p-4 flex justify-between items-center text-sm text-sky-300">
          <span>Currently viewing findings for a specific scan.</span>
          <button
            onClick={clearFilters}
            className="text-sky-400 hover:text-sky-300 font-medium underline"
          >
            View all findings
          </button>
        </div>
      )}

      {/* Findings Table */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
        </div>
      ) : findings.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-xl p-12 text-center bg-slate-900/50">
          <h3 className="text-xl font-medium text-white mb-2">No findings match criteria</h3>
          <p className="text-slate-400 max-w-md mx-auto text-sm">
            {repositoryId || severity || type || status || riskLevel || priority
              ? 'Try modifying your filters to view more findings.'
              : 'Secure! No security issues have been identified yet.'}
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs font-semibold uppercase text-slate-500 tracking-wider bg-slate-950/40 border-b border-slate-800">
                  <th className="text-left px-5 py-4">Priority</th>
                  <th className="text-left px-5 py-4">Score & Level</th>
                  <th className="text-left px-5 py-4">Vulnerability / Secret</th>
                  <th className="text-left px-5 py-4">Package / Rule</th>
                  <th className="text-left px-5 py-4">Repository</th>
                  <th className="text-left px-5 py-4">Location</th>
                  <th className="text-left px-5 py-4">Scanner</th>
                  <th className="text-left px-5 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {findings.map((finding) => {
                  const repo = repositories.find((r) => r.id === finding.repository_id);
                  const isSecret = finding.type === 'SECRET';
                  return (
                    <tr
                      key={finding.id}
                      className="hover:bg-slate-800/20 transition-colors"
                    >
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span
                          className={`px-2.5 py-1 rounded-md border text-xs font-mono font-bold ${getPriorityBadgeClass(
                            finding.priority
                          )}`}
                        >
                          {finding.priority || 'P3'}
                        </span>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-white font-mono text-sm">{finding.risk_score ?? 0}</span>
                          <span
                            className={`px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase ${getRiskLevelBadgeClass(
                              finding.risk_level
                            )}`}
                          >
                            {finding.risk_level || 'INFO'}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center space-x-2">
                          {isSecret ? (
                            <KeyRound className="w-4 h-4 text-amber-400 shrink-0" />
                          ) : (
                            <Package className="w-4 h-4 text-sky-400 shrink-0" />
                          )}
                          <div className="min-w-0">
                            <div className="text-white font-medium text-sm truncate max-w-xs" title={finding.title}>
                              {finding.vulnerability_id || finding.title}
                            </div>
                            {finding.vulnerability_id && (
                              <div className="text-xs text-slate-400 truncate max-w-xs">{finding.title}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-slate-300 text-xs font-mono">
                        {isSecret ? (
                          <span className="text-amber-300 font-semibold">{finding.rule_id || 'secret'}</span>
                        ) : (
                          <span>
                            <strong className="text-white font-semibold">{finding.package_name || '—'}</strong>
                            {finding.installed_version && <span className="text-slate-400"> {finding.installed_version}</span>}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-slate-400">
                        <div className="flex items-center space-x-1.5">
                          <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                          <span>{repo?.name || 'Unknown'}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-slate-400 font-mono text-xs truncate max-w-[160px]" title={finding.file_path}>
                        {finding.file_path || '—'}
                        {finding.line_number ? `:${finding.line_number}` : ''}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-slate-400 text-xs uppercase font-mono">
                        {finding.scanner}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap text-right">
                        <Link
                          to={`/findings/${finding.id}`}
                          className="text-sky-400 hover:text-sky-300 text-xs font-medium transition-colors inline-flex items-center space-x-1"
                        >
                          <span>Details →</span>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default FindingsPage;
