import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Loader2,
  Pencil,
  Trash2,
  ScanSearch,
  FolderGit2,
  GitBranch,
  CalendarDays,
  Clock,
  Info,
} from 'lucide-react';
import { Repository } from '../types';
import repositoryService from '../services/repositories';
import RepositoryFormModal from '../components/RepositoryFormModal';
import DeleteRepositoryModal from '../components/DeleteRepositoryModal';
import { useToast } from '../components/Toast';

function formatMonthYear(dateString: string): string {
  return new Date(dateString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
  });
}

export const RepositoryDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [repository, setRepository] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const repo = await repositoryService.get(id);
        setRepository(repo);
      } catch {
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-3" />
        <span className="text-sm font-medium">Loading repository...</span>
      </div>
    );
  }

  if (notFound || !repository) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center space-y-4">
          <h1 className="text-lg font-semibold text-slate-200">Repository not found</h1>
          <p className="text-sm text-slate-400">
            This repository does not exist or you do not have access to it.
          </p>
          <Link
            to="/repositories"
            className="inline-flex items-center space-x-2 text-sm text-sky-400 hover:text-sky-300 font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to repositories</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Back Link */}
      <Link
        to="/repositories"
        className="inline-flex items-center space-x-2 text-sm text-slate-400 hover:text-slate-200 font-medium transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to repositories</span>
      </Link>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">{repository.name}</h1>
            {!repository.is_active && (
              <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                Inactive
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <FolderGit2 className="w-4 h-4 text-slate-500" />
            <span className="font-medium text-slate-300">GitHub</span>
          </div>
          <a
            href={repository.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-sky-400 hover:text-sky-300 transition-colors break-all"
          >
            {repository.url}
          </a>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            onClick={() => setShowEditModal(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <Pencil className="w-4 h-4" />
            <span>Edit</span>
          </button>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="flex items-center space-x-1.5 px-3.5 py-2 text-sm font-medium text-red-400 hover:text-red-300 bg-red-950/40 hover:bg-red-950/70 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <GitBranch className="w-4 h-4" />
            <span>Default branch</span>
          </div>
          <div className="text-lg font-semibold text-white">{repository.default_branch}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <CalendarDays className="w-4 h-4" />
            <span>Added</span>
          </div>
          <div className="text-lg font-semibold text-white">
            {formatMonthYear(repository.created_at)}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Clock className="w-4 h-4" />
            <span>Last scan</span>
          </div>
          <div className="text-lg font-semibold text-white">
            {repository.last_scan_at
              ? new Date(repository.last_scan_at).toLocaleDateString()
              : 'Never'}
          </div>
        </div>
      </div>

      {/* Description */}
      {repository.description && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Description
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">{repository.description}</p>
        </div>
      )}

      {/* Scan Placeholder */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-4">
        <button
          disabled
          className="px-6 py-3 bg-sky-600 text-white text-sm font-semibold rounded-lg shadow-sm opacity-50 cursor-not-allowed inline-flex items-center space-x-2"
        >
          <ScanSearch className="w-4 h-4" />
          <span>Scan Repository</span>
        </button>
        <div className="flex items-center justify-center space-x-2 text-sm text-slate-400">
          <Info className="w-4 h-4 text-sky-500/80 shrink-0" />
          <span>Repository scanning will be available in the next version.</span>
        </div>
      </div>

      {/* Modals */}
      {showEditModal && (
        <RepositoryFormModal
          repository={repository}
          onClose={() => setShowEditModal(false)}
          onSaved={(updated) => {
            setRepository(updated);
            setShowEditModal(false);
            showToast('success', `Repository "${updated.name}" updated successfully.`);
          }}
        />
      )}
      {showDeleteModal && (
        <DeleteRepositoryModal
          repository={repository}
          onClose={() => setShowDeleteModal(false)}
          onDeleted={(deleted) => {
            showToast('success', `Repository "${deleted.name}" deleted successfully.`);
            navigate('/repositories');
          }}
          onError={(message) => {
            setShowDeleteModal(false);
            showToast('error', message);
          }}
        />
      )}
    </div>
  );
};

export default RepositoryDetailPage;
