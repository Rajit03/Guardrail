import React, { useState } from 'react';
import { X, Loader2, AlertCircle } from 'lucide-react';
import { AxiosError } from 'axios';
import { Repository, RepositoryCreatePayload, RepositoryUpdatePayload, ApiError } from '../types';
import repositoryService from '../services/repositories';

interface RepositoryFormModalProps {
  repository?: Repository;
  onClose: () => void;
  onSaved: (repository: Repository) => void;
}

const GITHUB_URL_REGEX = /^https:\/\/github\.com\/[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\/[A-Za-z0-9._-]{1,100}\/?$/;

function extractApiError(err: unknown): string {
  const axiosErr = err as AxiosError<ApiError>;
  const detail = axiosErr.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg).join(' ');
  }
  return 'Something went wrong. Please try again.';
}

export const RepositoryFormModal: React.FC<RepositoryFormModalProps> = ({
  repository,
  onClose,
  onSaved,
}) => {
  const isEdit = !!repository;

  const [name, setName] = useState(repository?.name ?? '');
  const [url, setUrl] = useState(repository?.url ?? '');
  const [defaultBranch, setDefaultBranch] = useState(repository?.default_branch ?? 'main');
  const [description, setDescription] = useState(repository?.description ?? '');
  const [isActive, setIsActive] = useState(repository?.is_active ?? true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Repository name is required.');
      return;
    }
    if (trimmedName.length > 100) {
      setError('Repository name must be at most 100 characters.');
      return;
    }
    if (!isEdit && !GITHUB_URL_REGEX.test(url.trim())) {
      setError('Please enter a valid GitHub repository URL, e.g. https://github.com/owner/repository');
      return;
    }
    if (!defaultBranch.trim()) {
      setError('Default branch is required.');
      return;
    }

    try {
      setSubmitting(true);
      let saved: Repository;
      if (isEdit) {
        const payload: RepositoryUpdatePayload = {
          name: trimmedName,
          default_branch: defaultBranch.trim(),
          description: description.trim() || null,
          is_active: isActive,
        };
        saved = await repositoryService.update(repository.id, payload);
      } else {
        const payload: RepositoryCreatePayload = {
          name: trimmedName,
          url: url.trim(),
          provider: 'github',
          default_branch: defaultBranch.trim(),
          ...(description.trim() ? { description: description.trim() } : {}),
        };
        saved = await repositoryService.create(payload);
      }
      onSaved(saved);
    } catch (err) {
      setError(extractApiError(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={isEdit ? 'Edit Repository' : 'Add Repository'}
    >
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">
            {isEdit ? 'Edit Repository' : 'Add Repository'}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-red-950/50 border border-red-800/60 rounded-lg p-3 flex items-start space-x-3 text-red-300 text-sm">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="repo-name">
              Repository Name
            </label>
            <input
              id="repo-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="backend-api"
              maxLength={100}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="repo-url">
              Repository URL
            </label>
            <input
              id="repo-url"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/example/backend-api"
              disabled={isEdit}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            />
            {isEdit && (
              <p className="text-xs text-slate-500 mt-1.5">
                The repository URL cannot be changed.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="repo-provider">
              Provider
            </label>
            <select
              id="repo-provider"
              value="github"
              disabled
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 text-sm disabled:opacity-80"
            >
              <option value="github">GitHub</option>
            </select>
            <p className="text-xs text-slate-500 mt-1.5">
              GitHub is the first supported provider. More providers coming soon.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="repo-branch">
              Default Branch
            </label>
            <input
              id="repo-branch"
              type="text"
              value={defaultBranch}
              onChange={(e) => setDefaultBranch(e.target.value)}
              placeholder="main"
              maxLength={255}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="repo-description">
              Description
            </label>
            <textarea
              id="repo-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
              maxLength={1000}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm transition-all resize-none"
            />
          </div>

          {isEdit && (
            <div className="flex items-center justify-between px-1">
              <label className="text-sm font-medium text-slate-300" htmlFor="repo-active">
                Active
              </label>
              <input
                id="repo-active"
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="w-4 h-4 accent-sky-500"
              />
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>{isEdit ? 'Save Changes' : 'Add Repository'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RepositoryFormModal;
