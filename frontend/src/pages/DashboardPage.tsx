import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, FolderGit2, AlertTriangle, ShieldCheck, Inbox } from 'lucide-react';
import { repositoryService } from '../services/repository';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [repoCount, setRepoCount] = useState<number>(0);

  useEffect(() => {
    const fetchRepoCount = async () => {
      try {
        const repos = await repositoryService.getRepositories();
        setRepoCount(repos.length);
      } catch (error) {
        console.error('Failed to fetch repository count', error);
      }
    };
    fetchRepoCount();
  }, []);

  const metrics = [
    {
      title: 'Security Score',
      value: '--',
      subtitle: 'No scans yet',
      icon: Shield,
      color: 'text-slate-400',
    },
    {
      title: 'Repositories',
      value: repoCount.toString(),
      subtitle: 'Connected repositories',
      icon: FolderGit2,
      color: 'text-sky-400',
      link: '/repositories',
    },
    {
      title: 'Open Findings',
      value: '0',
      subtitle: 'Active security alerts',
      icon: AlertTriangle,
      color: 'text-slate-400',
    },
    {
      title: 'Critical Findings',
      value: '0',
      subtitle: 'Immediate action items',
      icon: ShieldCheck,
      color: 'text-severity-critical',
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-5 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Guardrail
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Welcome, <span className="text-slate-200 font-semibold">{user?.name}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const CardContent = (
            <div
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700/80 transition-all flex flex-col justify-between h-full"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {metric.title}
                </span>
                <Icon className={`w-4 h-4 ${metric.color}`} />
              </div>
              <div className="mt-4">
                <div className="text-3xl font-bold text-white tracking-tight">
                  {metric.value}
                </div>
                <div className="text-xs text-slate-500 mt-1 font-medium">
                  {metric.subtitle}
                </div>
              </div>
            </div>
          );

          if (metric.link) {
            return (
              <Link to={metric.link} key={metric.title} className="block cursor-pointer">
                {CardContent}
              </Link>
            );
          }

          return <div key={metric.title}>{CardContent}</div>;
        })}
      </div>

      {/* Empty State Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center flex flex-col items-center justify-center space-y-4">
        <div className="w-14 h-14 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center text-slate-500 shadow-inner">
          <Inbox className="w-7 h-7 text-sky-500/80" />
        </div>
        <div className="space-y-1.5 max-w-md">
          <h2 className="text-lg font-semibold text-slate-200">
            No security scans yet.
          </h2>
          <p className="text-sm text-slate-400 leading-relaxed">
            Your security insights will appear here once you connect a repository.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
