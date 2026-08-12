import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderGit2, Loader2, Pencil, Trash2, Eye } from 'lucide-react';
import { Repository } from '../types';
import repositoryService from '../services/repositories';
import RepositoryFormModal from '../components/RepositoryFormModal';
import DeleteRepositoryModal from '../components/DeleteRepositoryModal';
import { useToast } from '../components/Toast';

function displayUrl(url: string): string {
  return url.replace(/^https:\/\//, '');
}

function formatLastScan(lastScanAt: string | null): string {
  if (!lastScanAt) return 'Never';
  return new Date(lastScanAt).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export const RepositoriesPage: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editTarget, setEditTarget] = useState<Repository | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Repository | null>(null);

  const navigate = useNavigate();
  const { showToast } = useToast();

  const loadRepositories = async () => {
    try {
      setLoading(true);
      setLoadError(null);
      const repos = await repositoryService.list();
      setRepositories(repos);
    } catch {
      setLoadError('Failed to load repositories. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  const handleCreated = (repository: Repository) => {
    setRepositories((prev) => [repository, ...prev]);
    setShowAddModal(false);
    showToast('success', `Repository "${repository.name}" added successfully.`);
  };

  const handleUpdated = (repository: Repository) => {
    setRepositories((prev) => prev.map((r) => (r.id === repository.id ? repository : r)));
    setEditTarget(null);
    showToast('success', `Repository "${repository.name}" updated successfully.`);
  };

  const handleDeleted = (repository: Repository) => {
    setRepositories((prev) => prev.filter((r) => r.id !== repository.id));
    setDeleteTarget(null);
    showToast('success', `Repository "${repository.name}" deleted successfully.`);
  };

  const addButton = (
    <button
      onClick={() => setShowAddModal(true)}
      className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-2"
    >
      <Plus className="w-4 h-4" />
      <span>Add Repository</span>
    </button>
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Repositories</h1>
          <p className="text-slate-400 text-sm mt-1">
            Manage the repositories connected to Guardrail.
          </p>
        </div>
        {repositories.length > 0 && addButton}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20 text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin mr-3" />
          <span className="text-sm font-medium">Loading repositories...</span>
        </div>
      )}

      {!loading && loadError && (
        <div className="bg-red-950/50 border border-red-800/60 rounded-lg p-4 text-red-300 text-sm flex items-center justify-between">
          <span>{loadError}</span>
          <button
            onClick={loadRepositories}
            className="text-sm font-medium text-red-200 hover:text-white underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !loadError && repositories.length === 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-5">
          <div className="w-14 h-14 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center shadow-inner">
            <FolderGit2 className="w-7 h-7 text-sky-500/80" />
          </div>
          <div className="space-y-1.5 max-w-md">
            <h2 className="text-lg font-semibold text-slate-200">
              No repositories connected yet.
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              Connect your first repository to start monitoring its security posture.
            </p>
          </div>
          {addButton}
        </div>
      )}

      {/* Repository Cards */}
      {!loading && !loadError && repositories.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-base font-semibold text-white truncate">{repo.name}</h3>
                  {!repo.is_active && (
                    <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50 shrink-0">
                      Inactive
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 truncate">{displayUrl(repo.url)}</p>
              </div>

              <div className="space-y-1.5 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span className="text-slate-500">Provider</span>
                  <span className="text-slate-300 font-medium">GitHub</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Branch</span>
                  <span className="text-slate-300 font-medium">{repo.default_branch}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Last scan</span>
                  <span className="text-slate-300 font-medium">
                    {formatLastScan(repo.last_scan_at)}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-1 border-t border-slate-800/80">
                <button
                  onClick={() => navigate(`/repositories/${repo.id}`)}
                  className="flex-1 flex items-center justify-center space-x-1.5 px-3 py-2 mt-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View</span>
                </button>
                <button
                  onClick={() => setEditTarget(repo)}
                  className="flex-1 flex items-center justify-center space-x-1.5 px-3 py-2 mt-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  <span>Edit</span>
                </button>
                <button
                  onClick={() => setDeleteTarget(repo)}
                  className="flex-1 flex items-center justify-center space-x-1.5 px-3 py-2 mt-2 text-xs font-medium text-red-400 hover:text-red-300 bg-red-950/40 hover:bg-red-950/70 rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {showAddModal && (
        <RepositoryFormModal onClose={() => setShowAddModal(false)} onSaved={handleCreated} />
      )}
      {editTarget && (
        <RepositoryFormModal
          repository={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={handleUpdated}
        />
      )}
      {deleteTarget && (
        <DeleteRepositoryModal
          repository={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={handleDeleted}
          onError={(message) => {
            setDeleteTarget(null);
            showToast('error', message);
          }}
        />
      )}
    </div>
  );
};

export default RepositoriesPage;
