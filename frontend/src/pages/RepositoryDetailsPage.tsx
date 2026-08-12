import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { FolderGit2, ArrowLeft, ExternalLink, Activity, Github, Settings, Trash2, ShieldAlert } from 'lucide-react';
import { repositoryService } from '../services/repository';
import { Repository } from '../types';

export const RepositoryDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchRepository = async () => {
      if (!id) return;
      try {
        const data = await repositoryService.getRepository(id);
        setRepository(data);
      } catch (error) {
        console.error('Failed to fetch repository', error);
        navigate('/repositories'); // Redirect on error/not found
      } finally {
        setLoading(false);
      }
    };
    fetchRepository();
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!id) return;
    setDeleting(true);
    try {
      await repositoryService.deleteRepository(id);
      navigate('/repositories');
    } catch (error) {
      console.error('Failed to delete repository', error);
      setDeleting(false);
      setShowDeleteConfirm(false);
      // Ideally show a toast error here
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  if (!repository) {
    return null; // Handled by redirect in catch block
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/repositories')}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
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
          <Link
            to={`/repositories/${repository.id}/edit`}
            className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-medium border border-slate-700 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Edit</span>
          </Link>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-red-500/10 text-slate-300 hover:text-red-400 px-4 py-2 rounded-lg text-sm font-medium border border-slate-700 hover:border-red-500/30 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="md:col-span-2 space-y-6">
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
                <a 
                  href={repository.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1.5 text-sky-400 hover:text-sky-300 transition-colors"
                >
                  <span>{repository.url}</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>

              <div>
                <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Description</span>
                <p className="text-slate-300">
                  {repository.description || <span className="text-slate-600 italic">No description provided</span>}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-white flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-indigo-400" />
                <span>Security Scanning</span>
              </h2>
              <span className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold uppercase tracking-wider">
                Phase 3
              </span>
            </div>
            
            <p className="text-slate-400 mb-6 text-sm">
              Repository scanning will be available in the next version. Guardrail will automatically analyze this repository for vulnerabilities, secrets, and misconfigurations.
            </p>

            <div className="flex justify-center">
              <button 
                disabled
                className="inline-flex items-center space-x-2 bg-slate-800 text-slate-500 px-6 py-3 rounded-lg font-medium border border-slate-700 cursor-not-allowed opacity-80 w-full justify-center"
              >
                <Activity className="w-5 h-5" />
                <span>Scan Repository</span>
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar details */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Status</span>
              <div className="flex items-center space-x-2">
                <span className={`w-2.5 h-2.5 rounded-full ${repository.is_active ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
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
              <span className="text-slate-300">
                {new Date(repository.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'long',
                })}
              </span>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Last Scan</span>
              <span className="text-slate-300">
                {repository.last_scan_at ? new Date(repository.last_scan_at).toLocaleString() : 'Never'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl">
            <h3 className="text-xl font-bold text-white mb-2">Delete Repository?</h3>
            <div className="text-slate-400 space-y-3 mb-6 text-sm">
              <p>
                Are you sure you want to remove <span className="font-semibold text-white">"{repository.name}"</span> from Guardrail?
              </p>
              <p>This action cannot be undone.</p>
            </div>
            
            <div className="flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="inline-flex items-center space-x-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 px-4 py-2 rounded-lg text-sm font-medium border border-red-500/20 transition-colors disabled:opacity-50"
              >
                {deleting ? (
                  <div className="w-4 h-4 border-2 border-red-500/20 border-t-red-500 rounded-full animate-spin"></div>
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
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
