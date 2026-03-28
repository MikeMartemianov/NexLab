import { useState, useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { 
  FileCode, MessageSquare, Activity, Settings, 
  Terminal as TerminalIcon, FolderTree, Plus, 
  Cpu, Zap, Shield, ChevronRight, ChevronDown, 
  X, Save, Play, Boxes, CheckCircle2, Layout, Send
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

const SettingsModal = ({ config, onClose, onSave, isProjectWizard = false }: any) => {
  const [name, setName] = useState('MyAgentProject');
  const [path, setPath] = useState('');
  const [model, setModel] = useState(config.model || 'gpt-4o');
  const [provider, setProvider] = useState(config.provider || 'openai');
  const [apiKey, setApiKey] = useState(config.api_key || '');
  const [baseUrl, setBaseUrl] = useState(config.base_url || '');
  const [temp, setTemp] = useState(config.temperature || 0.7);

  const handleSubmit = () => {
    if (isProjectWizard) {
      onSave({ name, path, provider, model, api_key: apiKey, base_url: baseUrl, temperature: temp });
    } else {
      onSave({ provider, model, api_key: apiKey, base_url: baseUrl, temperature: temp, mentorEnabled: true, deepThinkerEnabled: true });
    }
  };

  return (
    <div className="modal-bg">
      <div className="modal-content" style={{ width: '500px' }}>
        <div className="modal-header">
          <span>{isProjectWizard ? "Initialize New Agent Project" : "Agent Configuration"}</span>
          <X size={18} style={{ cursor: 'pointer' }} onClick={onClose} />
        </div>
        <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          {isProjectWizard && (
            <>
              <div className="form-group">
                <label>Project Name</label>
                <input value={name} onChange={e => setName(e.target.value)} placeholder="MySuperAgent" />
              </div>
              <div className="form-group">
                <label>Creation Path (Empty for current root)</label>
                <input value={path} onChange={e => setPath(e.target.value)} placeholder="./my_agent" />
              </div>
              <hr style={{ borderColor: 'var(--border-muted)', margin: '20px 0' }} />
            </>
          )}

          <div className="form-group">
            <label>AI Provider</label>
            <select value={provider} onChange={e => setProvider(e.target.value)}>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama (Local)</option>
              <option value="anthropic">Anthropic</option>
              <option value="mistral">Mistral AI</option>
              <option value="custom">Custom Endpoint</option>
            </select>
          </div>
          <div className="form-group">
            <label>Model</label>
            <input value={model} onChange={e => setModel(e.target.value)} placeholder="e.g. gpt-4o, llama3" />
          </div>
          <div className="form-group">
            <label>API Key (Optional for local)</label>
            <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="sk-..." />
          </div>
          <div className="form-group">
            <label>Base URL (Optional)</label>
            <input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder="https://api.openai.com/v1" />
          </div>
          <div className="form-group">
            <label>Temperature ({temp})</label>
            <input type="range" min="0" max="1" step="0.1" value={temp} onChange={e => setTemp(parseFloat(e.target.value))} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit}>
            {isProjectWizard ? "Create & Scaffold" : "Save & Restart Kernel"}
          </button>
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
  const [showWizard, setShowWizard] = useState(false);
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
       setTerminalLog(p => [...p, `[UI] Saved ${activeFile}`]);
    } catch (e) { alert("Save failed"); }
  };

  const handleRunScript = async () => {
    if (!activeFile) return;
    setTerminalOpen(true);
    setTerminalLog(p => [...p, `[UI] Requesting execution for ${activeFile}...`]);
    try {
       const res = await apiPost<any>('/api/project/run', { script_path: activeFile });
       setTerminalLog(p => [...p, res.message || res.error]);
    } catch (e) {
       setTerminalLog(p => [...p, `[UI] Execution request failed: ${e}`]);
    }
  };

  const createProject = async (cfg: any) => {
    if (!cfg.path) cfg.path = `./${cfg.name.toLowerCase().replace(/\\s+/g, '_')}`;
    try {
      const res = await apiPost<any>('/api/project/create', cfg);
      setShowWizard(false);
      setTerminalLog(p => [...p, res.message || res.error]);
      fetchState();
      setView('explorer');
    } catch (e) { alert("Failed to create project"); }
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
      return { tsx: 'typescript', ts: 'typescript', js: 'javascript', py: 'python', css: 'css', html: 'html', json: 'json', yml: 'yaml', yaml: 'yaml' }[ext] || 'plaintext';
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
        <div className={`action-btn ${view === 'chat' ? 'active' : ''}`} onClick={() => setView('chat')} title="Built-in AI Assistant">
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
                {view === 'explorer' ? 'Explorer' : 'AI Assistant'}
              </div>
              
              <div className="sidebar-content">
                {view === 'explorer' && files.map(n => <FileTreeNode key={n.path} node={n} onSelect={handleSelectFile} />)}
                
                {view === 'chat' && (
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0 12px' }}>
                    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
                      {chatMsgs.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Hello! I'm your Built-in AI coding assistant. Ask me anything.</div>}
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
                  <div style={{ flex: 1 }} />
                  {/* Action Buttons above Editor */}
                  <div style={{ display: 'flex', alignItems: 'center', paddingRight: '16px', gap: '8px' }}>
                    <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 12px' }} onClick={handleRunScript}>
                       <Play size={14} /> Run
                    </button>
                  </div>
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
                  <p style={{ color: 'var(--text-muted)' }}>Workspace Orchestration & Agent Builder</p>
                </div>

                <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--accent-glow)', borderColor: 'var(--accent-base)' }}>
                  <div>
                    <h2 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>Create an AI Agent</h2>
                    <p style={{ margin: 0, color: 'var(--text-main)', opacity: 0.8 }}>No need to code everything from scratch. Configure endpoints, memory, and thoughts here.</p>
                  </div>
                  <button className="btn btn-primary" onClick={() => setShowWizard(true)} style={{ padding: '12px 24px', fontSize: '15px' }}>
                    <Plus size={18} style={{ verticalAlign: 'middle', marginRight: '6px' }}/> New Agent
                  </button>
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
                  <h3 style={{ marginTop: 0, marginBottom: 20, color: 'var(--text-muted)', fontSize: 14 }}>Built-in AI Kernel Status</h3>
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
      {showWizard && <SettingsModal config={{}} isProjectWizard={true} onClose={() => setShowWizard(false)} onSave={createProject} />}
    </div>
  );
}
