import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Github, Save, ArrowLeft, AlertCircle } from 'lucide-react';
import { repositoryService } from '../services/repository';

export const AddRepositoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    provider: 'github',
    default_branch: 'main',
    description: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await repositoryService.createRepository(formData);
      navigate('/repositories');
    } catch (err: any) {
      console.error(err);
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          setError(err.response.data.detail.map((d: any) => d.msg).join(', '));
        } else {
          setError(err.response.data.detail);
        }
      } else {
        setError('Failed to add repository. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate('/repositories')}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Add Repository</h1>
          <p className="text-slate-400 mt-1">Connect a new repository to Guardrail.</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg flex items-start space-x-3 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-1.5">
                Repository Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                required
                value={formData.name}
                onChange={handleChange}
                placeholder="e.g., backend-api"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              />
            </div>

            <div>
              <label htmlFor="url" className="block text-sm font-medium text-slate-300 mb-1.5">
                Repository URL
              </label>
              <input
                id="url"
                name="url"
                type="url"
                required
                value={formData.url}
                onChange={handleChange}
                placeholder="https://github.com/example/backend-api"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="provider" className="block text-sm font-medium text-slate-300 mb-1.5">
                  Provider
                </label>
                <div className="relative">
                  <select
                    id="provider"
                    name="provider"
                    value={formData.provider}
                    disabled
                    className="w-full bg-slate-950/50 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-slate-400 appearance-none cursor-not-allowed opacity-80"
                  >
                    <option value="github">GitHub</option>
                  </select>
                  <Github className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Currently only GitHub is supported.</p>
              </div>

              <div>
                <label htmlFor="default_branch" className="block text-sm font-medium text-slate-300 mb-1.5">
                  Default Branch
                </label>
                <input
                  id="default_branch"
                  name="default_branch"
                  type="text"
                  required
                  value={formData.default_branch}
                  onChange={handleChange}
                  placeholder="main"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-slate-300 mb-1.5">
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                value={formData.description}
                onChange={handleChange}
                placeholder="Brief description of this repository"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-colors resize-none"
              ></textarea>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => navigate('/repositories')}
              className="px-4 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white px-5 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              ) : (
                <Save className="w-4 h-4" />
              )}
              <span>Add Repository</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddRepositoryPage;
