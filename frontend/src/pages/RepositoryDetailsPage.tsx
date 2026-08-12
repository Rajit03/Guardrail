import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  FolderGit2, ArrowLeft, ExternalLink, Github, Settings, Trash2,
  ShieldAlert, Play, Clock, CheckCircle, XCircle, Loader2, AlertCircle
} from 'lucide-react';
import { repositoryService } from '../services/repository';
import { scanService } from '../services/scan';
import { Repository, Scan } from '../types';

export const RepositoryDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;
      try {
        const [repo, repoScans] = await Promise.all([
          repositoryService.getRepository(id),
          repositoryService.getRepositoryScans(id)
        ]);
        setRepository(repo);
        // Sort scans desc by started_at
        const sortedScans = [...repoScans].sort((a, b) => {
          const aTime = new Date(a.started_at || a.created_at || '').getTime();
          const bTime = new Date(b.started_at || b.created_at || '').getTime();
          return bTime - aTime;
        });
        setScans(sortedScans);
      } catch {
        navigate('/repositories');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  const handleScan = async () => {
    if (!id) return;
    setScanning(true);
    setScanError(null);
    try {
      await scanService.scanRepository(id);
      // Refresh repo and scans from the API
      const [updatedRepo, updatedScans] = await Promise.all([
        repositoryService.getRepository(id),
        repositoryService.getRepositoryScans(id)
      ]);
      setRepository(updatedRepo);
      setScans(updatedScans.sort((a, b) => {
        const aTime = new Date(a.started_at || a.created_at || '').getTime();
        const bTime = new Date(b.started_at || b.created_at || '').getTime();
        return bTime - aTime;
      }));
    } catch (err: any) {
      setScanError(
        err.response?.data?.detail || 'Scan failed. Please verify the repository is publicly accessible.'
      );
    } finally {
      setScanning(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    setDeleting(true);
    try {
      await repositoryService.deleteRepository(id);
      navigate('/repositories');
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!repository) return null;

  const scanStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'FAILED': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'RUNNING': return <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />;
      default: return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/repositories')} className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center space-x-2">
              <FolderGit2 className="w-6 h-6 text-sky-400" />
              <span>{repository.name}</span>
            </h1>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Link to={`/repositories/${repository.id}/edit`} className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-medium border border-slate-700 transition-colors">
            <Settings className="w-4 h-4" />
            <span>Edit</span>
          </Link>
          <button onClick={() => setShowDeleteConfirm(true)} className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-red-500/10 text-slate-300 hover:text-red-400 px-4 py-2 rounded-lg text-sm font-medium border border-slate-700 hover:border-red-500/30 transition-colors">
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="md:col-span-2 space-y-6">
          {/* Details card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-medium text-white mb-4">Repository Details</h2>
            <div className="space-y-4">
              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Provider</span>
                <div className="flex items-center space-x-2 text-slate-300">
                  {repository.provider === 'github' && <Github className="w-5 h-5" />}
                  <span className="capitalize">{repository.provider}</span>
                </div>
              </div>
              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">URL</span>
                <a href={repository.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center space-x-1.5 text-sky-400 hover:text-sky-300 transition-colors">
                  <span>{repository.url}</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Description</span>
                <p className="text-slate-300">{repository.description || <span className="text-slate-600 italic">No description</span>}</p>
              </div>
            </div>
          </div>

          {/* Scan section */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-white flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-indigo-400" />
                <span>Security Scanning</span>
              </h2>
            </div>

            {scanError && (
              <div className="mb-4 bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg flex items-start space-x-2 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{scanError}</span>
              </div>
            )}

            <button
              onClick={handleScan}
              disabled={scanning}
              className="w-full inline-flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {scanning ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Scanning repository...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  <span>Scan Repository</span>
                </>
              )}
            </button>

            {scanning && (
              <div className="mt-4 space-y-1.5 text-sm text-slate-400">
                <p className="flex items-center space-x-2"><Loader2 className="w-3 h-3 animate-spin text-sky-400" /><span>Preparing repository...</span></p>
                <p className="flex items-center space-x-2"><Loader2 className="w-3 h-3 animate-spin text-sky-400" /><span>Running secret scanner...</span></p>
                <p className="flex items-center space-x-2"><Loader2 className="w-3 h-3 animate-spin text-sky-400" /><span>Running dependency scanner...</span></p>
              </div>
            )}
          </div>

          {/* Scan History */}
          {scans.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h2 className="text-lg font-medium text-white">Scan History</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs font-semibold uppercase text-slate-500 tracking-wider bg-slate-950/30">
                    <th className="text-left px-6 py-3">Date</th>
                    <th className="text-left px-6 py-3">Status</th>
                    <th className="text-left px-6 py-3">Findings</th>
                    <th className="text-left px-6 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {scans.map(scan => (
                    <tr key={scan.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-3 text-slate-300">
                        {scan.completed_at ? new Date(scan.completed_at).toLocaleString() : '—'}
                      </td>
                      <td className="px-6 py-3">
                        <span className="flex items-center space-x-1.5">
                          {scanStatusIcon(scan.status)}
                          <span className={`capitalize ${scan.status === 'COMPLETED' ? 'text-emerald-400' : scan.status === 'FAILED' ? 'text-red-400' : 'text-sky-400'}`}>
                            {scan.status.toLowerCase()}
                          </span>
                        </span>
                      </td>
                      <td className="px-6 py-3 text-slate-300">{scan.status === 'COMPLETED' ? scan.total_findings : '—'}</td>
                      <td className="px-6 py-3">
                        {scan.status === 'COMPLETED' && scan.total_findings > 0 && (
                          <Link to={`/findings?scan_id=${scan.id}`} className="text-sky-400 hover:text-sky-300 text-xs font-medium transition-colors">
                            View findings →
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Status</span>
              <div className="flex items-center space-x-2">
                <span className={`w-2.5 h-2.5 rounded-full ${repository.is_active ? 'bg-emerald-500' : 'bg-slate-500'}`} />
                <span className="text-slate-300">{repository.is_active ? 'Active' : 'Inactive'}</span>
              </div>
            </div>
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Default Branch</span>
              <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300 font-mono text-sm">
                {repository.default_branch}
              </span>
            </div>
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Added</span>
              <span className="text-slate-300">{new Date(repository.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })}</span>
            </div>
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Last Scan</span>
              <span className="text-slate-300">{repository.last_scan_at ? new Date(repository.last_scan_at).toLocaleString() : 'Never'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Delete modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-xl font-bold text-white mb-2">Delete Repository?</h3>
            <div className="text-slate-400 space-y-3 mb-6 text-sm">
              <p>Are you sure you want to remove <span className="font-semibold text-white">"{repository.name}"</span> from Guardrail?</p>
              <p>This action cannot be undone. All associated scans and findings will also be deleted.</p>
            </div>
            <div className="flex items-center justify-end space-x-3">
              <button onClick={() => setShowDeleteConfirm(false)} disabled={deleting} className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">Cancel</button>
              <button onClick={handleDelete} disabled={deleting} className="inline-flex items-center space-x-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 px-4 py-2 rounded-lg text-sm font-medium border border-red-500/20 transition-colors disabled:opacity-50">
                {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                <span>Delete Repository</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RepositoryDetailsPage;
