import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ShieldAlert, Filter, RefreshCw, FolderGit2 } from 'lucide-react';
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
        // If scan_id is in URL, fetch findings just for that scan
        data = await scanService.getScanFindings(scanId);
      } else {
        const filters: FindingFilters = {};
        if (repositoryId) filters.repository_id = repositoryId;
        if (severity) filters.severity = severity;
        if (type) filters.type = type;
        if (status) filters.status = status;
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
  }, [repositoryId, severity, type, status, scanId]);

  const handleFilterChange = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    // If changing other filters, clear scan_id filter to show general list
    if (key !== 'scan_id') {
      newParams.delete('scan_id');
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'HIGH':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LOW':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-sky-400" />
            <span>Security Findings</span>
          </h1>
          <p className="text-slate-400 mt-1">
            {scanId ? 'Findings detected in this scan.' : 'Vulnerabilities and security issues detected across your repositories.'}
          </p>
        </div>
        <button
          onClick={fetchFindings}
          className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white px-3 py-2 rounded-lg text-sm font-medium border border-slate-800 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Bar */}
      {!scanId && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2 text-slate-400 text-sm">
            <Filter className="w-4 h-4" />
            <span>Filters:</span>
          </div>

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

          {/* Severity Filter */}
          <select
            value={severity}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
            <option value="INFO">Info</option>
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

          {(repositoryId || severity || type || status) && (
            <button
              onClick={clearFilters}
              className="text-xs text-sky-400 hover:text-sky-300 font-medium ml-auto"
            >
              Clear all filters
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

      {/* Findings Table/List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
        </div>
      ) : findings.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-xl p-12 text-center bg-slate-900/50">
          <h3 className="text-xl font-medium text-white mb-2">No findings found</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            {repositoryId || severity || type || status
              ? 'Try modifying your filters to see more findings.'
              : 'Secure! No security issues have been identified yet.'}
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs font-semibold uppercase text-slate-500 tracking-wider bg-slate-950/30 border-b border-slate-800">
                  <th className="text-left px-6 py-4">Severity</th>
                  <th className="text-left px-6 py-4">Type</th>
                  <th className="text-left px-6 py-4">Finding</th>
                  <th className="text-left px-6 py-4">Repository</th>
                  <th className="text-left px-6 py-4">File</th>
                  <th className="text-left px-6 py-4">Scanner</th>
                  <th className="text-left px-6 py-4">Status</th>
                  <th className="text-left px-6 py-4">Detected</th>
                  <th className="text-left px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {findings.map((finding) => {
                  const repo = repositories.find((r) => r.id === finding.repository_id);
                  return (
                    <tr
                      key={finding.id}
                      className="hover:bg-slate-800/20 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded-full border text-xs font-semibold ${getSeverityBadgeClass(
                            finding.severity
                          )}`}
                        >
                          {finding.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-300 font-medium">
                        {finding.type}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-white font-medium max-w-xs truncate" title={finding.title}>
                          {finding.title}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                        <div className="flex items-center space-x-1.5">
                          <FolderGit2 className="w-3.5 h-3.5 text-slate-500" />
                          <span>{repo?.name || 'Unknown'}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400 font-mono text-xs truncate max-w-[180px]" title={finding.file_path}>
                        {finding.file_path || '—'}
                        {finding.line_number ? `:${finding.line_number}` : ''}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-400 text-xs uppercase">
                        {finding.scanner}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="flex items-center space-x-1.5 text-slate-300">
                          <span className={`w-2 h-2 rounded-full ${finding.status === 'OPEN' ? 'bg-amber-500' : 'bg-slate-500'}`}></span>
                          <span className="capitalize">{finding.status.toLowerCase().replace('_', ' ')}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-500 text-xs">
                        {new Date(finding.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <Link
                          to={`/findings/${finding.id}`}
                          className="text-sky-400 hover:text-sky-300 text-xs font-medium transition-colors"
                        >
                          Details →
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
