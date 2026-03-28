import { useState, useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { 
  FileCode, MessageSquare, Activity, Settings, 
  Terminal as TerminalIcon, FolderTree, 
  Cpu, Zap, Shield, ChevronRight, ChevronDown, 
  X, Save, Play, Boxes, CheckCircle2, Layout, Send, Layers, Share2
} from 'lucide-react';
import NodeEditor from './components/NodeEditor';

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

interface FileNode { name: string; path: string; type: 'file' | 'directory'; children?: FileNode[]; }
interface ChatMessage { role: 'user' | 'assistant'; content: string; thinking?: string; }

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

const SettingsModal = ({ defaultConf, onClose, onSave, isProjectWizard = false }: any) => {
  const [tab, setTab] = useState('basic');
  
  // State initialization with advanced config keys
  const [cfg, setCfg] = useState({
    name: 'MySuperAgent',
    path: '',
    provider: defaultConf?.provider || 'openai',
    model: defaultConf?.model || 'gpt-4o',
    api_key: defaultConf?.api_key || '',
    base_url: defaultConf?.base_url || '',
    temperature: defaultConf?.temperature ?? 0.7,
    top_p: 0.9,
    max_response_length: 8000,
    language: 'en',
    tone: 'neutral',
    verbose_level: 1,
    mentor_enabled: true,
    deep_thinker_enabled: true,
    fast_memory_enabled: true,
    memory_max_items: 100,
    memory_retention_days: 30,
    enable_logging: true,
    log_level: 'INFO'
  });

  const update = (k: string, v: any) => setCfg(prev => ({ ...prev, [k]: v }));

  const handleSubmit = () => {
    if (isProjectWizard) {
      onSave(cfg);
    } else {
      // Internal system agent config (mostly API / model details)
      onSave({ 
        provider: cfg.provider, model: cfg.model, 
        api_key: cfg.api_key, base_url: cfg.base_url, 
        temperature: cfg.temperature, 
        mentorEnabled: cfg.mentor_enabled, deepThinkerEnabled: cfg.deep_thinker_enabled 
      });
    }
  };

  return (
    <div className="modal-bg">
      <div className="modal-content" style={{ width: isProjectWizard ? '700px' : '450px' }}>
        <div className="modal-header">
          <span>{isProjectWizard ? "Agent Blueprint / Advanced Config" : "System AI Configuration"}</span>
          <X size={18} style={{ cursor: 'pointer' }} onClick={onClose} />
        </div>
        
        {isProjectWizard && (
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-muted)', background: 'var(--bg-base)' }}>
             {['basic', 'model', 'modules', 'memory', 'system'].map(t => (
                <div key={t} onClick={() => setTab(t)} style={{ padding: '12px 16px', fontSize: '12px', cursor: 'pointer', textTransform: 'uppercase', color: tab === t ? 'var(--accent-base)' : 'var(--text-dim)', borderBottom: tab === t ? '2px solid var(--accent-base)' : '2px solid transparent' }}>
                  {t}
                </div>
             ))}
          </div>
        )}

        <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          {(!isProjectWizard || tab === 'basic') && isProjectWizard && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Project Name</label>
                <input value={cfg.name} onChange={e => update('name', e.target.value)} />
              </div>
              <div className="form-group">
                <label>Target Path (Empty for current workspace)</label>
                <input value={cfg.path} onChange={e => update('path', e.target.value)} placeholder="./my_agent" />
              </div>
            </div>
          )}

          {(!isProjectWizard || tab === 'model') && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>AI Provider</label>
                <select value={cfg.provider} onChange={e => update('provider', e.target.value)}>
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama (Local)</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="mistral">Mistral AI</option>
                  <option value="custom">Custom Endpoint</option>
                </select>
              </div>
              <div className="form-group">
                <label>Model</label>
                <input value={cfg.model} onChange={e => update('model', e.target.value)} />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>API Key</label>
                <input type="password" value={cfg.api_key} onChange={e => update('api_key', e.target.value)} placeholder="sk-..." />
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label>Base URL</label>
                <input value={cfg.base_url} onChange={e => update('base_url', e.target.value)} placeholder="https://api.openai.com/v1" />
              </div>
              <div className="form-group">
                <label>Temperature ({cfg.temperature})</label>
                <input type="range" min="0" max="1" step="0.1" value={cfg.temperature} onChange={e => update('temperature', parseFloat(e.target.value))} />
              </div>
              {isProjectWizard && (
                <div className="form-group">
                  <label>Top P ({cfg.top_p})</label>
                  <input type="range" min="0" max="1" step="0.1" value={cfg.top_p} onChange={e => update('top_p', parseFloat(e.target.value))} />
                </div>
              )}
            </div>
          )}

          {isProjectWizard && tab === 'modules' && (
             <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
               <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <input type="checkbox" checked={cfg.mentor_enabled} onChange={e => update('mentor_enabled', e.target.checked)} /> Enable AI Mentor Module
               </label>
               <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <input type="checkbox" checked={cfg.deep_thinker_enabled} onChange={e => update('deep_thinker_enabled', e.target.checked)} /> Enable Deep Thinker Reasoning
               </label>
               <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <input type="checkbox" checked={cfg.fast_memory_enabled} onChange={e => update('fast_memory_enabled', e.target.checked)} /> Enable Fast Memory Assist
               </label>
             </div>
          )}

          {isProjectWizard && tab === 'memory' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                 <label>Language</label>
                 <input value={cfg.language} onChange={e => update('language', e.target.value)} placeholder="en" />
              </div>
              <div className="form-group">
                 <label>Max Response Length</label>
                 <input type="number" value={cfg.max_response_length} onChange={e => update('max_response_length', parseInt(e.target.value))} />
              </div>
              <div className="form-group">
                 <label>Memory Items Limit</label>
                 <input type="number" value={cfg.memory_max_items} onChange={e => update('memory_max_items', parseInt(e.target.value))} />
              </div>
              <div className="form-group">
                 <label>Memory Retention (Days)</label>
                 <input type="number" value={cfg.memory_retention_days} onChange={e => update('memory_retention_days', parseInt(e.target.value))} />
              </div>
            </div>
          )}

          {isProjectWizard && tab === 'system' && (
             <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
               <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <input type="checkbox" checked={cfg.enable_logging} onChange={e => update('enable_logging', e.target.checked)} /> Enable Logging
               </label>
               <div className="form-group">
                 <label>Log Level</label>
                 <select value={cfg.log_level} onChange={e => update('log_level', e.target.value)}>
                   <option value="DEBUG">Debug</option>
                   <option value="INFO">Info</option>
                   <option value="WARNING">Warning</option>
                   <option value="ERROR">Error</option>
                 </select>
               </div>
             </div>
          )}

        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSubmit}>
            {isProjectWizard ? "Scaffold AI Agent" : "Apply to System"}
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
  
  const [projectStats, setProjectStats] = useState<any>(null);
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [internalAgentConfig, setInternalAgentConfig] = useState<any>(null);

  const [showConfig, setShowConfig] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [showStudio, setShowStudio] = useState(false);
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
    } catch (e) { }
  }, []);

  const fetchInternalConfig = async () => {
    try {
      const resp = await apiGet<any>('/api/agent/config');
      setInternalAgentConfig(resp);
    } catch(e) {}
  };

  useEffect(() => {
    fetchState();
    fetchInternalConfig();
    const t = setInterval(fetchState, 5000);
    return () => clearInterval(t);
  }, [fetchState]);

  const handleSelectFile = async (path: string) => {
    try {
      const res = await apiGet<any>(`/api/file?path=${encodeURIComponent(path)}`);
      setFileContent(res.content || '');
      setActiveFile(path);
      if (!openTabs.includes(path)) setOpenTabs([...openTabs, path]);
    } catch (e) { }
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
    } catch (e) { }
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
    const payload = {
      name: cfg.name,
      path: cfg.path ? cfg.path : `./${cfg.name.toLowerCase().replace(/\\s+/g, '_')}`,
      config: cfg
    };
    try {
      const res = await apiPost<any>('/api/project/create', payload);
      setShowWizard(false);
      setTerminalLog(p => [...p, res.message || res.error]);
      fetchState();
      setView('explorer');
    } catch (e) { alert("Failed to create project"); }
  };

  const saveInternalConfig = async (cfg: any) => {
    try {
      await apiPost('/api/agent/configure', cfg);
      setShowConfig(false);
      fetchInternalConfig();
      setTerminalLog(p => [...p, "[System] AI Kernel reconfigured"]);
    } catch (e) { alert("Failed to configure AI"); }
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

  const getLang = (path: string) => {
      const ext = path.split('.').pop() || '';
      return { tsx: 'typescript', ts: 'typescript', js: 'javascript', py: 'python', css: 'css', html: 'html', json: 'json', yml: 'yaml', yaml: 'yaml', txt: 'plaintext' }[ext] || 'plaintext';
  };

  return (
    <div className="app-layout">
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
          {(view === 'explorer' || view === 'chat') && (
            <div className="sidebar-panel">
              <div className="sidebar-header">{view === 'explorer' ? 'Explorer' : 'AI Assistant'}</div>
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
                  <div style={{ display: 'flex', alignItems: 'center', paddingRight: '16px', gap: '8px' }}>
                    <button className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 12px' }} onClick={handleRunScript}>
                       <Play size={14} /> Run
                    </button>
                  </div>
                </div>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Editor theme="vs-dark" language={getLang(activeFile)} path={activeFile} value={fileContent} onChange={v => setFileContent(v || '')} options={{ minimap: { enabled: false }, fontSize: 13, padding: { top: 16 } }} />
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
                    <h2 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>Advanced Agent Blueprint</h2>
                    <p style={{ margin: 0, color: 'var(--text-main)', opacity: 0.8 }}>Design incredibly powerful AI agents via our advanced configuration system, fully abstracted from the code.</p>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn btn-secondary" onClick={() => setShowWizard(true)} style={{ padding: '12px 24px', fontSize: '15px' }}>
                      <Layers size={18} style={{ verticalAlign: 'middle', marginRight: '6px' }}/> Agent Wizard
                    </button>
                    <button className="btn btn-primary" onClick={() => setShowStudio(true)} style={{ padding: '12px 24px', fontSize: '15px' }}>
                      <Share2 size={18} style={{ verticalAlign: 'middle', marginRight: '6px' }}/> Node Studio
                    </button>
                  </div>
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
                  <h3 style={{ marginTop: 0, marginBottom: 20, color: 'var(--text-muted)', fontSize: 14 }}>System Engine Status</h3>
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

      {showConfig && <SettingsModal defaultConf={internalAgentConfig || {}} onClose={() => setShowConfig(false)} onSave={saveInternalConfig} />}
      {showWizard && <SettingsModal isProjectWizard={true} onClose={() => setShowWizard(false)} onSave={createProject} />}
      <NodeEditor isVisible={showStudio} onClose={() => setShowStudio(false)} />
    </div>
  );
}
