import { useState, useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { 
  FileCode, MessageSquare, Activity, Settings, 
  Terminal as TerminalIcon, FolderTree, 
  Cpu, Zap, Shield, ChevronRight, ChevronDown, 
  X, Save, Boxes, CheckCircle2, Layout, Send
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed`);
  return res.json();
}

async function apiPost<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed`);
  return res.json();
}

// --- Types ---
interface FileNode { name: string; path: string; type: 'file' | 'directory'; children?: FileNode[]; }
interface ChatMessage { role: 'user' | 'assistant'; content: string; thinking?: string; }

// --- Components ---
const FileTreeNode = ({ node, onSelect }: { node: FileNode; onSelect: (path: string) => void }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isDir = node.type === 'directory';

  return (
    <div style={{ paddingLeft: '8px' }}>
      <div className="tree-item" onClick={() => isDir ? setIsOpen(!isOpen) : onSelect(node.path)}>
        {isDir ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <FileCode size={14} />}
        {node.name}
      </div>
      {isDir && isOpen && node.children && (
        <div style={{ marginLeft: '4px', borderLeft: '1px solid var(--border-muted)' }}>
          {node.children.map(child => <FileTreeNode key={child.path} node={child} onSelect={onSelect} />)}
        </div>
      )}
    </div>
  );
};

const SettingsModal = ({ config, onClose, onSave }: any) => {
  const [model, setModel] = useState(config.model || 'gpt-4o');
  const [provider, setProvider] = useState(config.provider || 'openai');
  const [temp, setTemp] = useState(config.temperature || 0.7);

  return (
    <div className="modal-bg">
      <div className="modal-content">
        <div className="modal-header">
          <span>Agent Configuration</span>
          <X size={18} style={{ cursor: 'pointer' }} onClick={onClose} />
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>AI Provider</label>
            <select value={provider} onChange={e => setProvider(e.target.value)}>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama (Local)</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>
          <div className="form-group">
            <label>Model</label>
            <input value={model} onChange={e => setModel(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Temperature ({temp})</label>
            <input type="range" min="0" max="1" step="0.1" value={temp} onChange={e => setTemp(parseFloat(e.target.value))} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={() => onSave({ provider, model, temperature: temp, mentorEnabled: true, deepThinkerEnabled: true })}>Save & Restart</button>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [view, setView] = useState<'home' | 'explorer' | 'chat'>('home');
  const [files, setFiles] = useState<FileNode[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  
  // Real Data State
  const [projectStats, setProjectStats] = useState<any>(null);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [showConfig, setShowConfig] = useState(false);
  const [terminalOpen, setTerminalOpen] = useState(false);
  
  const [chatMsgs, setChatMsgs] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [terminalLog, setTerminalLog] = useState<string[]>(['NexLab Kernel v1.0 Ready.']);
  const [termInput, setTermInput] = useState('');

  const fetchState = useCallback(async () => {
    try {
      const f = await apiGet<any>('/api/files');
      if (f.files) setFiles(f.files);
      const s = await apiGet<any>('/api/project/stats');
      setProjectStats(s);
      const ag = await apiGet<any>('/api/agent/status');
      setAgentStatus(ag);
    } catch (e) {
      console.warn("Backend fetch failed", e);
    }
  }, []);

  useEffect(() => {
    fetchState();
    const t = setInterval(fetchState, 5000);
    return () => clearInterval(t);
  }, [fetchState]);

  const handleSelectFile = async (path: string) => {
    try {
      const res = await apiGet<any>(`/api/file?path=${encodeURIComponent(path)}`);
      setFileContent(res.content || '');
      setActiveFile(path);
      if (!openTabs.includes(path)) setOpenTabs([...openTabs, path]);
    } catch (e) { console.error("Could not load file"); }
  };

  const closeTab = (e: any, path: string) => {
    e.stopPropagation();
    const newTabs = openTabs.filter(t => t !== path);
    setOpenTabs(newTabs);
    if (activeFile === path) setActiveFile(newTabs.length ? newTabs[newTabs.length - 1] : null);
  };

  const handleSave = async () => {
    if (!activeFile) return;
    try {
       await apiPost('/api/file/save', { path: activeFile, content: fileContent });
    } catch (e) { alert("Save failed"); }
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput;
    setChatMsgs(p => [...p, { role: 'user', content: msg }]);
    setChatInput('');
    try {
      const res = await apiPost<any>('/api/chat', { message: msg });
      setChatMsgs(p => [...p, { role: 'assistant', content: res.reply, thinking: res.thinking }]);
    } catch (e) {
      setChatMsgs(p => [...p, { role: 'assistant', content: "[Backend AI Error]" }]);
    }
  };

  const handleTermCommand = async (e: any) => {
    if (e.key === 'Enter' && termInput.trim()) {
      const cmd = termInput;
      setTerminalLog(p => [...p, `❯ ${cmd}`]);
      setTermInput('');
      try {
        const res = await apiPost<any>('/api/terminal/exec', { command: cmd });
        setTerminalLog(p => [...p, res.output]);
      } catch (e) {
        setTerminalLog(p => [...p, `Error executing command.`]);
      }
    }
  };

  const saveConfig = async (cfg: any) => {
    try {
      await apiPost('/api/agent/configure', cfg);
      setShowConfig(false);
      fetchState();
    } catch (e) { alert("Failed to configure AI"); }
  };

  const getLang = (path: string) => {
      const ext = path.split('.').pop() || '';
      return { tsx: 'typescript', ts: 'typescript', js: 'javascript', py: 'python', css: 'css', html: 'html', json: 'json' }[ext] || 'plaintext';
  };

  return (
    <div className="app-layout">
      {/* Activity Bar */}
      <div className="activity-bar">
        <div className={`action-btn ${view === 'home' ? 'active' : ''}`} onClick={() => setView('home')} title="Dashboard">
          <Layout size={22} />
        </div>
        <div className={`action-btn ${view === 'explorer' ? 'active' : ''}`} onClick={() => setView('explorer')} title="Explorer">
          <FolderTree size={22} />
        </div>
        <div className={`action-btn ${view === 'chat' ? 'active' : ''}`} onClick={() => setView('chat')} title="AI Chat">
          <MessageSquare size={22} />
        </div>
        
        <div className="spacer" />
        
        <div className={`action-btn ${terminalOpen ? 'active' : ''}`} onClick={() => setTerminalOpen(!terminalOpen)} title="Terminal">
          <TerminalIcon size={22} />
        </div>
        <div className="action-btn" onClick={() => setShowConfig(true)} title="Settings">
          <Settings size={22} />
        </div>
      </div>

      <div className="main-area">
        <div className="workspace-container">
          
          {/* Side Panel */}
          {(view === 'explorer' || view === 'chat') && (
            <div className="sidebar-panel">
              <div className="sidebar-header">
                {view === 'explorer' ? 'Explorer' : 'Agent Chat'}
              </div>
              
              <div className="sidebar-content">
                {view === 'explorer' && files.map(n => <FileTreeNode key={n.path} node={n} onSelect={handleSelectFile} />)}
                
                {view === 'chat' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0 12px' }}>
                    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
                      {chatMsgs.map((m, i) => (
                        <div key={i} style={{ 
                          background: m.role === 'user' ? 'var(--bg-elevated)' : 'var(--accent-glow)', 
                          padding: '10px 14px', borderRadius: '12px', alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                          border: m.role === 'assistant' ? '1px solid var(--accent-base)' : '1px solid var(--border-muted)',
                          maxWidth: '90%'
                        }}>
                          {m.content}
                          {m.thinking && <div style={{ marginTop: 8, fontSize: 11, fontStyle: 'italic', opacity: 0.7 }}>Thought: {m.thinking}</div>}
                        </div>
                      ))}
                    </div>
                    <div style={{ padding: '12px 0', borderTop: '1px solid var(--border-muted)', display: 'flex', gap: '8px' }}>
                      <input style={{ flex: 1, background: 'var(--bg-elevated)', border: 'none', color: '#fff', padding: '8px 12px', borderRadius: '8px', outline: 'none' }}
                        value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleChat()} placeholder="Instruct Agent..." />
                      <button className="btn btn-primary" style={{ padding: '8px 12px' }} onClick={handleChat}><Send size={16}/></button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Central Area */}
          <div className="content-view">
            {activeFile ? (
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <div className="tabs-header">
                  {openTabs.map(t => (
                    <div key={t} className={`tab ${activeFile === t ? 'active' : ''}`} onClick={() => setActiveFile(t)}>
                      <FileCode size={14} /> {t.split('/').pop()}
                      <X size={14} className="close-btn" onClick={(e) => closeTab(e, t)} />
                    </div>
                  ))}
                </div>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Editor
                    theme="vs-dark"
                    language={getLang(activeFile)}
                    path={activeFile}
                    value={fileContent}
                    onChange={v => setFileContent(v || '')}
                    options={{ minimap: { enabled: false }, fontSize: 13, padding: { top: 16 } }}
                  />
                  <button className="floating-save" onClick={handleSave}><Save size={20}/></button>
                </div>
              </div>
            ) : (
              <div className="home-view">
                <div className="home-header">
                  <h1>NexLab AI 1.0</h1>
                  <p style={{ color: 'var(--text-muted)' }}>Workspace Orchestration Center</p>
                </div>

                <div className="glass-card">
                  <h3 style={{ marginTop: 0, marginBottom: 20, color: 'var(--text-muted)', fontSize: 14 }}>Realtime Telemetry</h3>
                  <div className="stats-row">
                    <div className="stat-item">
                      <div className="stat-icon"><FolderTree size={24} /></div>
                      <div className="stat-details"><h4>Project Root</h4><p style={{fontSize: 18}}>{projectStats?.projectName || 'Loading...'}</p></div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-icon"><FileCode size={24} /></div>
                      <div className="stat-details"><h4>Tracked Files</h4><p>{projectStats?.fileCount ?? 0}</p></div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-icon"><Activity size={24} /></div>
                      <div className="stat-details"><h4>Project Volume</h4><p>{projectStats?.totalSizeKb ?? 0} KB</p></div>
                    </div>
                  </div>
                </div>

                <div className="glass-card">
                  <h3 style={{ marginTop: 0, marginBottom: 20, color: 'var(--text-muted)', fontSize: 14 }}>AI Kernel Status</h3>
                  <div className="stats-row">
                    <div className="stat-item">
                      <div className="stat-icon" style={{ background: agentStatus?.state === 'ready' ? 'rgba(16,185,129,0.2)' : 'var(--bg-elevated)', color: agentStatus?.state === 'ready' ? 'var(--success)' : 'var(--text-dim)' }}><Cpu size={24} /></div>
                      <div className="stat-details"><h4>Core Engine</h4><p style={{fontSize: 16, textTransform: 'capitalize'}}>{agentStatus?.state || 'Offline'}</p></div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-icon" style={{ background: 'rgba(99,102,241,0.2)', color: 'var(--accent-base)' }}><Shield size={24} /></div>
                      <div className="stat-details"><h4>Mentor Module</h4><p style={{fontSize: 16, textTransform: 'capitalize'}}>{agentStatus?.mentor_state || 'Standby'}</p></div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-icon" style={{ background: 'rgba(245,158,11,0.2)', color: 'var(--warning)' }}><Zap size={24} /></div>
                      <div className="stat-details"><h4>Deep Thinker</h4><p style={{fontSize: 16, textTransform: 'capitalize'}}>{agentStatus?.deep_thinker_state || 'Sleeping'}</p></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Terminal Dock */}
        {terminalOpen && (
          <div className="bottom-dock">
            <div className="dock-header">
              <span>NEXLAB TERMINAL</span>
              <X size={14} style={{ cursor: 'pointer' }} onClick={() => setTerminalOpen(false)} />
            </div>
            <div className="terminal-container">
              {terminalLog.map((l, i) => <div key={i} className="terminal-line">{l}</div>)}
              <div className="terminal-input-wrap">
                <span>❯</span>
                <input autoFocus value={termInput} onChange={e => setTermInput(e.target.value)} onKeyDown={handleTermCommand} />
              </div>
            </div>
          </div>
        )}

        <div className="status-bar">
          <div style={{ display: 'flex', gap: '16px' }}>
            <div className="status-item"><CheckCircle2 size={13} color="var(--success)" /> Connected: {API_BASE}</div>
            <div className="status-item"><Boxes size={13} /> FW: v{agentStatus?.version || '1.0'}</div>
          </div>
          <div className="status-item">{activeFile ? getLang(activeFile) : 'Dashboard'}</div>
        </div>
      </div>

      {showConfig && <SettingsModal config={{}} onClose={() => setShowConfig(false)} onSave={saveConfig} />}
    </div>
  );
}
