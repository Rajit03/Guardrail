import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FolderGit2, FileText, Flame, CheckCircle, RefreshCw, Package } from 'lucide-react';
import { findingService, riskService } from '../services/scan';
import { repositoryService } from '../services/repository';
import { Finding, Repository, RiskAssessment } from '../types';

export const FindingDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [finding, setFinding] = useState<Finding | null>(null);
  const [repository, setRepository] = useState<Repository | null>(null);
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);

  const fetchFindingDetails = async () => {
    if (!id) return;
    try {
      const data = await findingService.getFinding(id);
      setFinding(data);
      if (data.risk_assessment) {
        setRiskAssessment(data.risk_assessment);
      } else {
        try {
          const riskData = await riskService.getFindingRisk(id);
          setRiskAssessment(riskData);
        } catch {
          // ignore
        }
      }
      const repo = await repositoryService.getRepository(data.repository_id);
      setRepository(repo);
    } catch (error) {
      console.error('Failed to fetch finding details', error);
      navigate('/findings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindingDetails();
  }, [id, navigate]);

  const handleRecalculateRisk = async () => {
    if (!id) return;
    setRecalculating(true);
    try {
      const updatedRisk = await riskService.recalculateFindingRisk(id);
      setRiskAssessment(updatedRisk);
      const updatedFinding = await findingService.getFinding(id);
      setFinding(updatedFinding);
    } catch (err) {
      console.error('Failed to recalculate risk', err);
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!finding) return null;

  const isSecret = finding.type === 'SECRET';
  const isDependency = finding.type === 'DEPENDENCY';

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

  const getSeverityBadgeClass = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'HIGH': return 'bg-orange-500/10 text-orange-400 border-orange-500/20';
      case 'MEDIUM': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'LOW': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {isSecret ? 'Secret Finding Details' : 'Dependency Finding Details'}
              </span>
              {finding.vulnerability_id && (
                <span className="bg-slate-800 text-sky-400 text-xs px-2 py-0.5 rounded font-mono font-semibold">
                  {finding.vulnerability_id}
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight truncate max-w-xl" title={finding.title}>
              {finding.title}
            </h1>
          </div>
        </div>

        <button
          onClick={handleRecalculateRisk}
          disabled={recalculating}
          className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white px-3.5 py-2 rounded-lg text-sm font-medium border border-slate-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${recalculating ? 'animate-spin' : ''}`} />
          <span>Recalculate Risk</span>
        </button>
      </div>

      {/* Risk Engine Banner */}
      {riskAssessment && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white flex items-center space-x-2">
              <Flame className="w-5 h-5 text-rose-500" />
              <span>Risk Engine Assessment</span>
            </h2>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded-md border text-sm font-mono font-bold ${getPriorityBadgeClass(riskAssessment.priority)}`}>
                {riskAssessment.priority}
              </span>
              <span className={`px-3 py-1 rounded-full border text-xs font-bold ${getRiskLevelBadgeClass(riskAssessment.risk_level)}`}>
                {riskAssessment.risk_level}
              </span>
            </div>
          </div>

          {/* Risk Score Gauge & Factors */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div className="md:col-span-1 border-b md:border-b-0 md:border-r border-slate-800/80 pb-4 md:pb-0 md:pr-4 flex flex-col justify-center items-center text-center">
              <span className="text-xs uppercase tracking-wider font-semibold text-slate-500">Risk Score</span>
              <div className="text-4xl font-extrabold text-white tracking-tight mt-1">
                {riskAssessment.risk_score} <span className="text-xs font-normal text-slate-500">/ 100</span>
              </div>
            </div>

            <div className="md:col-span-3 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <span className="text-slate-500 block mb-0.5 font-medium">Severity Baseline</span>
                <span className="font-mono text-slate-200 font-semibold">{riskAssessment.factors.severity} / 100</span>
              </div>
              <div>
                <span className="text-slate-500 block mb-0.5 font-medium">Exploitability</span>
                <span className="font-mono text-slate-200 font-semibold">{riskAssessment.factors.exploitability}</span>
              </div>
              <div>
                <span className="text-slate-500 block mb-0.5 font-medium">Exposure</span>
                <span className="font-mono text-slate-200 font-semibold">{riskAssessment.factors.exposure}</span>
              </div>
              <div>
                <span className="text-slate-500 block mb-0.5 font-medium">Asset Criticality</span>
                <span className="font-mono text-slate-200 font-semibold">{riskAssessment.factors.asset_criticality}</span>
              </div>
              <div>
                <span className="text-slate-500 block mb-0.5 font-medium">Confidence</span>
                <span className="font-mono text-slate-200 font-semibold">{riskAssessment.factors.confidence}</span>
              </div>
            </div>
          </div>

          {/* Explanation */}
          {riskAssessment.explanation && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Why is this risky?</h3>
              <p className="text-slate-300 text-sm leading-relaxed bg-slate-950/40 p-3.5 rounded-lg border border-slate-800/60">
                {riskAssessment.explanation}
              </p>
            </div>
          )}

          {/* Recommended Action */}
          {riskAssessment.recommended_action && (
            <div className="space-y-1.5">
              <h3 className="text-xs font-semibold text-sky-400 uppercase tracking-wider flex items-center space-x-1.5">
                <CheckCircle className="w-4 h-4 text-sky-400" />
                <span>Recommended Action</span>
              </h3>
              <pre className="text-slate-200 text-xs leading-relaxed bg-slate-950/60 p-4 rounded-lg border border-slate-800/80 font-sans whitespace-pre-wrap">
                {riskAssessment.recommended_action}
              </pre>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="md:col-span-2 space-y-6">
          {/* Dependency specific metadata */}
          {isDependency && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
                <Package className="w-4 h-4 text-sky-400" />
                <span>Dependency Information</span>
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Package</span>
                  <span className="font-semibold text-white">{finding.package_name || '—'}</span>
                </div>
                <div>
                  <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Installed Version</span>
                  <span className="font-mono text-slate-300">{finding.installed_version || '—'}</span>
                </div>
                <div>
                  <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Ecosystem</span>
                  <span className="font-mono text-slate-300">PyPI / npm</span>
                </div>
                <div>
                  <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Fixed Version</span>
                  <span className="font-mono text-emerald-400 font-semibold">{finding.fixed_version || 'Patched release required'}</span>
                </div>
                {finding.vulnerability_id && (
                  <div>
                    <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Vulnerability ID</span>
                    <span className="font-mono text-sky-400">{finding.vulnerability_id}</span>
                  </div>
                )}
                {finding.aliases && finding.aliases.length > 0 && (
                  <div>
                    <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Aliases</span>
                    <div className="flex flex-wrap gap-1">
                      {finding.aliases.map((alias) => (
                        <span key={alias} className="bg-slate-950 px-2 py-0.5 rounded text-xs font-mono text-slate-400 border border-slate-800">
                          {alias}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

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
                {isSecret && (
                  <p className="text-[11px] text-slate-500 mt-1">
                    Sensitive credential values are automatically masked by Guardrail to protect your secrets.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
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
              </div>
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default FindingDetailsPage;
