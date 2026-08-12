import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  FolderGit2, 
  AlertTriangle, 
  Bot, 
  Settings, 
  LogOut, 
  User as UserIcon 
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', active: true },
    { name: 'Repositories', icon: FolderGit2, path: '/repositories', active: true },
    { name: 'Findings', icon: AlertTriangle, path: '#', active: false, badge: 'Coming soon' },
    { name: 'Copilot', icon: Bot, path: '#', active: false, badge: 'Coming soon' },
    { name: 'Settings', icon: Settings, path: '#', active: false, badge: 'Coming soon' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row font-sans">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0">
        <div>
          {/* Brand Header */}
          <div className="flex items-center space-x-3 px-3 py-4 mb-6 border-b border-slate-800">
            <span className="text-2xl" role="img" aria-label="shield">🛡️</span>
            <span className="text-xl font-bold tracking-tight text-white">Guardrail</span>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              if (item.active) {
                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-sky-950/60 text-sky-400 border-sky-800/40'
                          : 'text-slate-400 border-transparent hover:bg-slate-800/50 hover:text-slate-200'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <div className="flex items-center space-x-3">
                        <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                        <span>{item.name}</span>
                      </div>
                    )}
                  </NavLink>
                );
              }

              return (
                <div
                  key={item.name}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg text-slate-500 text-sm font-medium cursor-not-allowed select-none opacity-70"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4 text-slate-500" />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* User Info & Logout */}
        <div className="pt-4 border-t border-slate-800 space-y-3 mt-6">
          <div className="flex items-center space-x-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <UserIcon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate">{user?.name}</p>
              <p className="text-xs text-slate-400 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-slate-950 p-6 md:p-8">
        <Outlet />
      </main>
    </div>
  );
};

export default DashboardLayout;
