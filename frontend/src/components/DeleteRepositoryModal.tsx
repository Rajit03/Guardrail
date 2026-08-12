import React, { useState } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Repository } from '../types';
import repositoryService from '../services/repositories';

interface DeleteRepositoryModalProps {
  repository: Repository;
  onClose: () => void;
  onDeleted: (repository: Repository) => void;
  onError: (message: string) => void;
}

export const DeleteRepositoryModal: React.FC<DeleteRepositoryModalProps> = ({
  repository,
  onClose,
  onDeleted,
  onError,
}) => {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    try {
      setDeleting(true);
      await repositoryService.remove(repository.id);
      onDeleted(repository);
    } catch {
      onError('Failed to delete repository. Please try again.');
      setDeleting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Delete Repository"
    >
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-5">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-red-950/60 border border-red-800/50 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-5 h-5 text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-white">Delete Repository?</h2>
        </div>

        <p className="text-sm text-slate-400 leading-relaxed">
          Are you sure you want to remove{' '}
          <span className="text-slate-200 font-semibold">"{repository.name}"</span> from
          Guardrail?
        </p>
        <p className="text-sm text-red-400/90 font-medium">This action cannot be undone.</p>

        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={deleting}
            className="px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            className="px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {deleting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Deleting...</span>
              </>
            ) : (
              <span>Delete Repository</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteRepositoryModal;
