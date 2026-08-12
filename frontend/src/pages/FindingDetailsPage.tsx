import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FolderGit2, FileText } from 'lucide-react';
import { findingService } from '../services/scan';
import { repositoryService } from '../services/repository';
import { Finding, Repository } from '../types';

export const FindingDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [finding, setFinding] = useState<Finding | null>(null);
  const [repository, setRepository] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFindingDetails = async () => {
      if (!id) return;
      try {
        const data = await findingService.getFinding(id);
        setFinding(data);
        const repo = await repositoryService.getRepository(data.repository_id);
        setRepository(repo);
      } catch (error) {
        console.error('Failed to fetch finding details', error);
        navigate('/findings');
      } finally {
        setLoading(false);
      }
    };
    fetchFindingDetails();
  }, [id, navigate]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!finding) return null;

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
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Finding Details
            </span>
            <h1 className="text-xl font-bold text-white tracking-tight truncate max-w-xl" title={finding.title}>
              {finding.title}
            </h1>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="md:col-span-2 space-y-6">
          {/* Description & Evidence */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Description</h3>
              <p className="text-slate-200 leading-relaxed text-sm">
                {finding.description || 'No detailed description available.'}
              </p>
            </div>

            {finding.evidence && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Evidence</h3>
                <pre className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap break-all">
                  {finding.evidence}
                </pre>
                <p className="text-[11px] text-slate-500 mt-1">
                  Sensitive credential values are automatically masked by Guardrail to protect your secrets.
                </p>
              </div>
            )}

            {finding.recommendation && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Recommendation</h3>
                <p className="text-slate-200 leading-relaxed text-sm">
                  {finding.recommendation}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            {/* Status Dropdown / Action */}
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1.5">Status</span>
              <div className="relative">
                <select
                  disabled
                  value={finding.status}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-400 appearance-none cursor-not-allowed"
                >
                  <option value="OPEN">Open</option>
                  <option value="ACKNOWLEDGED">Acknowledged</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="FALSE_POSITIVE">False Positive</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-500">
                  <span className="text-[10px]">▼</span>
                </div>
              </div>
              <p className="text-[10px] text-slate-500 mt-1">Workflow automation coming in a future version.</p>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Severity</span>
              <span
                className={`inline-block px-2.5 py-0.5 rounded-full border text-xs font-semibold ${getSeverityBadgeClass(
                  finding.severity
                )}`}
              >
                {finding.severity}
              </span>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Type</span>
              <span className="text-sm font-semibold text-slate-300 capitalize">{finding.type.toLowerCase()}</span>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Repository</span>
              <div className="flex items-center space-x-1.5 text-slate-300 text-sm">
                <FolderGit2 className="w-4 h-4 text-sky-400" />
                <span>{repository?.name || 'Unknown'}</span>
              </div>
            </div>

            {finding.file_path && (
              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">File Location</span>
                <div className="flex items-start space-x-1.5 text-slate-300 text-sm font-mono break-all">
                  <FileText className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                  <span>
                    {finding.file_path}
                    {finding.line_number ? `:${finding.line_number}` : ''}
                  </span>
                </div>
              </div>
            )}

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Scanner</span>
              <span className="text-sm text-slate-300 uppercase">{finding.scanner}</span>
            </div>

            {finding.rule_id && (
              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Rule ID</span>
                <span className="text-xs text-slate-300 font-mono bg-slate-950 px-2 py-1 rounded border border-slate-800/80 inline-block max-w-full truncate" title={finding.rule_id}>
                  {finding.rule_id}
                </span>
              </div>
            )}

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Detected</span>
              <span className="text-sm text-slate-300">
                {new Date(finding.created_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FindingDetailsPage;
