import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderGit2, Plus, ExternalLink } from 'lucide-react';
import { repositoryService } from '../services/repository';
import { Repository } from '../types';

export const RepositoriesPage: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRepositories = async () => {
      try {
        const data = await repositoryService.getRepositories();
        setRepositories(data);
      } catch (error) {
        console.error('Failed to fetch repositories', error);
      } finally {
        setLoading(false);
      }
    };
    fetchRepositories();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Repositories</h1>
          <p className="text-slate-400 mt-1">Manage your connected code repositories.</p>
        </div>
        <Link
          to="/repositories/new"
          className="inline-flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Repository</span>
        </Link>
      </div>

      {repositories.length === 0 ? (
        <div className="border border-dashed border-slate-800 rounded-xl p-12 text-center bg-slate-900/50">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-800 mb-4">
            <FolderGit2 className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-xl font-medium text-white mb-2">No repositories connected yet.</h3>
          <p className="text-slate-400 max-w-md mx-auto mb-6">
            Connect your first repository to start monitoring its security posture.
          </p>
          <Link
            to="/repositories/new"
            className="inline-flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium border border-slate-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Add Repository</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors group flex flex-col"
            >
              <div className="p-5 flex-1">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center">
                      <FolderGit2 className="w-5 h-5 text-sky-400" />
                    </div>
                    <div>
                      <h3 className="text-white font-medium truncate" title={repo.name}>
                        {repo.name}
                      </h3>
                      <div className="flex items-center space-x-1 text-xs text-slate-500 mt-0.5">
                        <span>{repo.provider === 'github' ? 'GitHub' : repo.provider}</span>
                        <span>•</span>
                        <a 
                          href={repo.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="hover:text-sky-400 flex items-center space-x-1 transition-colors"
                        >
                          <span className="truncate max-w-[150px]">{repo.url.replace('https://', '')}</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 mb-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Branch</span>
                    <span className="text-slate-300 font-mono text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                      {repo.default_branch}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Last scan</span>
                    <span className="text-slate-300">
                      {repo.last_scan_at ? new Date(repo.last_scan_at).toLocaleString() : 'Never'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Findings</span>
                    <span className="flex items-center space-x-1.5 font-semibold">
                      {repo.findings_count > 0 ? (
                        <Link to={`/findings?repository_id=${repo.id}&status=OPEN`} className="text-amber-500 hover:underline">
                          {repo.findings_count} Open
                        </Link>
                      ) : (
                        <span className="text-emerald-400">0 Open</span>
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Scan Status</span>
                    <span className="flex items-center space-x-1.5">
                      {repo.last_scan_status ? (
                        <>
                          <span className={`w-2 h-2 rounded-full ${
                            repo.last_scan_status === 'COMPLETED' ? 'bg-emerald-500' :
                            repo.last_scan_status === 'FAILED' ? 'bg-red-500' : 'bg-sky-500 animate-pulse'
                          }`}></span>
                          <span className="text-slate-300 capitalize text-xs">{repo.last_scan_status.toLowerCase()}</span>
                        </>
                      ) : (
                        <span className="text-slate-500 italic text-xs">No scans yet</span>
                      )}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-800 p-3 bg-slate-900/50 flex justify-end space-x-2">
                <Link
                  to={`/repositories/${repo.id}`}
                  className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md transition-colors"
                >
                  View
                </Link>
                <Link
                  to={`/repositories/${repo.id}/edit`}
                  className="px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-md transition-colors"
                >
                  Edit
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RepositoriesPage;
