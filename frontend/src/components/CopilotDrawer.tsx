import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { copilotService } from '../services/copilot';
import { ChatMessage, CopilotHealthResponse, RelatedFindingItem } from '../types/copilot';

interface CopilotDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialRepositoryId?: string | null;
  initialRepositoryName?: string | null;
  initialFindingId?: string | null;
  initialFindingTitle?: string | null;
  initialPrompt?: string | null;
}

const DEFAULT_SUGGESTIONS = [
  'What should I fix first?',
  'How secure is my repository?',
  'Do I have exposed secrets?',
  'Which dependencies are vulnerable?',
  'What changed since my last scan?',
  'Give me a security summary',
];

export const CopilotDrawer: React.FC<CopilotDrawerProps> = ({
  isOpen,
  onClose,
  initialRepositoryId,
  initialRepositoryName,
  initialFindingId,
  initialFindingTitle,
  initialPrompt,
}) => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<CopilotHealthResponse | null>(null);
  const [activeRepoId, setActiveRepoId] = useState<string | null>(initialRepositoryId || null);
  const [activeRepoName, setActiveRepoName] = useState<string | null>(initialRepositoryName || null);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(initialFindingId || null);
  const [activeFindingTitle, setActiveFindingTitle] = useState<string | null>(initialFindingTitle || null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync props when drawer opens
  useEffect(() => {
    if (isOpen) {
      if (initialRepositoryId !== undefined) {
        setActiveRepoId(initialRepositoryId);
        setActiveRepoName(initialRepositoryName || null);
      }
      if (initialFindingId !== undefined) {
        setActiveFindingId(initialFindingId);
        setActiveFindingTitle(initialFindingTitle || null);
      }
      fetchHealth();
      if (initialPrompt) {
        handleSendMessage(initialPrompt);
      }
    }
  }, [isOpen, initialRepositoryId, initialFindingId, initialPrompt]);

  const fetchHealth = async () => {
    try {
      const res = await copilotService.getHealth();
      setHealth(res);
    } catch {
      setHealth({
        status: 'UNREACHABLE',
        reachable: false,
        model_available: false,
        model_name: 'llama3.2:1b',
        message: 'Ollama service is unreachable.',
      });
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsLoading(true);

    try {
      const resp = await copilotService.chat({
        message: query,
        repository_id: activeRepoId || undefined,
        finding_id: activeFindingId || undefined,
      });

      const copilotMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'copilot',
        text: resp.answer,
        recommended_actions: resp.recommended_actions,
        related_findings: resp.related_findings,
        model_used: resp.model_used,
        isFallback: resp.context_summary?.fallback,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, copilotMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'copilot',
        text: err.response?.data?.detail || 'Copilot encountered an error communicating with the AI service. Please verify your local Ollama connection.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await copilotService.clearHistory();
    } catch {}
    setMessages([]);
  };

  const handleFindingClick = (findingId: string) => {
    onClose();
    navigate(`/findings/${findingId}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full z-10">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 backdrop-blur">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white font-bold">
              ✦
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white tracking-wide">Guardrail Copilot</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {health?.model_name || 'llama3.2:1b'}
                </span>
              </div>
              <p className="text-xs text-slate-400">Contextual Security Advisor • Local AI</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Status indicator */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                health?.status === 'HEALTHY'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              }`}
              title={health?.message}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  health?.status === 'HEALTHY' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span className="text-[11px]">{health?.status === 'HEALTHY' ? 'Online' : 'Offline/Fallback'}</span>
            </div>

            <button
              onClick={handleClearHistory}
              title="Clear conversation"
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg text-xs transition"
            >
              Clear
            </button>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg text-sm transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Active Context Banner */}
        {(activeRepoName || activeFindingTitle) && (
          <div className="px-4 py-2 bg-indigo-950/40 border-b border-indigo-900/30 flex items-center justify-between text-xs text-indigo-300">
            <div className="flex items-center space-x-2 truncate">
              <span className="font-semibold text-indigo-400">Active Focus:</span>
              {activeRepoName && (
                <span className="bg-indigo-900/40 px-2 py-0.5 rounded border border-indigo-800/40 truncate">
                  Repo: {activeRepoName}
                </span>
              )}
              {activeFindingTitle && (
                <span className="bg-indigo-900/40 px-2 py-0.5 rounded border border-indigo-800/40 truncate">
                  Finding: {activeFindingTitle}
                </span>
              )}
            </div>
            <button
              onClick={() => {
                setActiveRepoId(null);
                setActiveRepoName(null);
                setActiveFindingId(null);
                setActiveFindingTitle(null);
              }}
              className="text-indigo-400 hover:text-white font-medium ml-2 shrink-0"
            >
              Clear Focus
            </button>
          </div>
        )}

        {/* Messages Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl">
                🛡️
              </div>
              <div className="max-w-md">
                <h3 className="text-sm font-bold text-white">Ask about your security posture</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Guardrail Copilot explains your real findings, evaluates priority risks, and provides actionable remediation guidance. Secrets are always masked.
                </p>
              </div>

              {/* Suggestions */}
              <div className="w-full max-w-md pt-2 space-y-1.5">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
                  Suggested Questions
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {DEFAULT_SUGGESTIONS.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(s)}
                      className="text-left px-3 py-2 rounded-lg bg-slate-800/60 hover:bg-indigo-600/20 border border-slate-700/50 hover:border-indigo-500/40 text-xs text-slate-300 hover:text-indigo-200 transition flex items-center justify-between group"
                    >
                      <span>{s}</span>
                      <span className="text-slate-500 group-hover:text-indigo-400 text-xs">→</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/10'
                        : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700/60 shadow-md'
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans text-slate-100">{msg.text}</div>

                    {/* Recommended Actions Section */}
                    {msg.recommended_actions && msg.recommended_actions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-700/60 space-y-1.5">
                        <div className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider flex items-center space-x-1">
                          <span>✓</span>
                          <span>Recommended Remediation Steps</span>
                        </div>
                        <ul className="space-y-1">
                          {msg.recommended_actions.map((act, i) => (
                            <li key={i} className="flex items-start space-x-2 text-slate-300">
                              <span className="text-indigo-400 font-bold">•</span>
                              <span>{act}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Related Findings Badges */}
                    {msg.related_findings && msg.related_findings.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-700/60 space-y-1.5">
                        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                          Referenced Findings ({msg.related_findings.length})
                        </div>
                        <div className="flex flex-col gap-1.5">
                          {msg.related_findings.map((rf: RelatedFindingItem) => (
                            <div
                              key={rf.id}
                              onClick={() => handleFindingClick(rf.id)}
                              className="p-2 rounded-lg bg-slate-900/80 hover:bg-indigo-950/60 border border-slate-700/60 hover:border-indigo-500/40 cursor-pointer transition flex items-center justify-between group"
                            >
                              <div className="truncate mr-2">
                                <div className="font-semibold text-white truncate text-[11px]">{rf.title}</div>
                                <div className="text-[10px] text-slate-400 truncate">
                                  {rf.file_path || rf.package_name || rf.type}
                                </div>
                              </div>
                              <div className="flex items-center space-x-1.5 shrink-0">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                                    rf.severity === 'CRITICAL'
                                      ? 'bg-rose-500/20 text-rose-400'
                                      : rf.severity === 'HIGH'
                                      ? 'bg-orange-500/20 text-orange-400'
                                      : 'bg-amber-500/20 text-amber-400'
                                  }`}
                                >
                                  {rf.severity}
                                </span>
                                <span className="text-[10px] font-mono text-indigo-400 font-semibold">
                                  {rf.priority}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                      <span>{msg.timestamp}</span>
                      {msg.sender === 'copilot' && (
                        <span className="font-mono text-[9px] text-slate-400">
                          {msg.model_used || 'llama3.2:1b'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex items-center space-x-2 text-xs text-indigo-400 bg-slate-800/60 p-3 rounded-2xl max-w-[80%] border border-slate-700/50">
                  <div className="w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
                  <span>Guardrail Copilot is analyzing your security data...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={
                activeFindingTitle
                  ? `Ask about "${activeFindingTitle.slice(0, 25)}..."`
                  : activeRepoName
                  ? `Ask about repo "${activeRepoName}"...`
                  : 'Ask about your security posture, findings, or fixes...'
              }
              className="flex-1 bg-slate-800 border border-slate-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 outline-none transition"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !inputQuery.trim()}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center space-x-1.5"
            >
              <span>Send</span>
              <span>↑</span>
            </button>
          </form>
          <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between px-1">
            <span>Authoritative facts derived directly from Guardrail Risk Engine</span>
            <span>Secrets always masked</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CopilotDrawer;
