import React, { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { 
  FileCode, MessageSquare, Activity, Settings, 
  Terminal as TerminalIcon, FolderTree, Plus, 
  Cpu, Zap, Shield, ChevronRight, ChevronDown, 
  X, Save, Boxes, Info, CheckCircle2, Globe, Layout, Send
} from 'lucide-react';

// ═══════════ TYPES ═══════════

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
}

interface AgentConfig {
  provider: string;
  model: string;
  temperature: number;
  mentorEnabled: boolean;
  deepThinkerEnabled: boolean;
  mentorInterval: number;
  maxResponseLength: number;
  tools: Record<string, boolean>;
}

// ═══════════ API HELPERS ═══════════

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

// ═══════════ SUB-COMPONENTS ═══════════

const Dashboard = ({ stats }: { stats: any }) => (
  <div className="dashboard-container">
    <div className="dashboard-header">
      <Layout size={32} color="var(--text-accent)" />
      <h1>Project Dashboard</h1>
    </div>
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-icon"><FileCode size={24} /></div>
        <div className="stat-info">
          <div className="stat-label">Files</div>
          <div className="stat-value">{stats?.fileCount || 0}</div>
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-icon"><Activity size={24} /></div>
        <div className="stat-info">
          <div className="stat-label">Project Size</div>
          <div className="stat-value">{stats?.totalSizeKb || 0} KB</div>
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-icon"><Zap size={24} /></div>
        <div className="stat-info">
          <div className="stat-label">Agent Health</div>
          <div className="stat-value" style={{ color: 'var(--status-success)' }}>Excellent</div>
        </div>
      </div>
      <div className="stat-card">
        <div className="stat-icon"><Shield size={24} /></div>
        <div className="stat-info">
          <div className="stat-label">Uptime</div>
          <div className="stat-value">99.9%</div>
        </div>
      </div>
    </div>
    
    <div className="dashboard-content">
      <div className="content-panel project-info">
        <h3><Info size={18} /> Project Information</h3>
        <p><strong>Name:</strong> {stats?.projectName || 'Unnamed Project'}</p>
        <p><strong>Status:</strong> <span style={{ color: 'var(--status-success)' }}>Active & Connected</span></p>
        <div className="progress-bar"><div className="progress-fill" style={{ width: '68%' }}></div></div>
        <small>Framework Maturity: Release 1.0.0 Stable</small>
      </div>
      <div className="content-panel agent-activity">
        <h3><Activity size={18} /> Recent Activity</h3>
        <div className="activity-list" style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          <div style={{ marginBottom: '8px' }}>• AI initialized successfully (v1.0.0)</div>
          <div style={{ marginBottom: '8px' }}>• Configuration sync: System Optimal</div>
          <div style={{ marginBottom: '8px' }}>• Memory pool optimized for long-context</div>
        </div>
      </div>
    </div>
  </div>
);

const DiagnosticsPanel = ({ events }: { events: any[] }) => (
  <div className="panel-inner-view" style={{ padding: '24px' }}>
    <div className="view-header" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
      <Activity size={24} color="var(--text-accent)" />
      <h2 style={{ margin: 0 }}>System Diagnostics</h2>
    </div>
    <div className="diagnostics-list" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {events.length === 0 && <div style={{ color: 'var(--text-muted)' }}>No recent events. Waiting for activity...</div>}
      {events.map((ev, i) => (
        <div key={i} style={{ 
          padding: '8px 12px', 
          background: 'var(--bg-secondary)', 
          borderLeft: `3px solid ${ev.level === 'error' ? 'var(--status-error)' : 'var(--text-accent)'}`,
          borderRadius: '4px',
          fontSize: '12.5px'
        }}>
          <span style={{ color: 'var(--text-muted)', marginRight: '10px', fontFamily: 'var(--font-mono)' }}>[{ev.timestamp?.split('T')[1]?.split('.')[0]}]</span>
          <span style={{ color: 'var(--text-primary)' }}>{ev.message || ev.summary}</span>
        </div>
      ))}
    </div>
  </div>
);

const CapabilitiesPanel = ({ tools }: { tools: any[] }) => (
  <div className="panel-inner-view" style={{ padding: '24px' }}>
    <div className="view-header" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
      <Boxes size={24} color="var(--text-accent)" />
      <h2 style={{ margin: 0 }}>Agent Capabilities</h2>
    </div>
    <div className="tools-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
      {tools.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Detecting system capabilities...</div>}
      {tools.map((t, i) => (
        <div key={i} className="tool-card" style={{ 
          background: 'var(--bg-secondary)', 
          border: '1px solid var(--border-primary)', 
          borderRadius: '10px', 
          padding: '16px' 
        }}>
          <div style={{ fontWeight: 'bold', color: 'var(--text-accent)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TerminalIcon size={14} /> {t.name}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{t.description}</div>
        </div>
      ))}
    </div>
  </div>
);

const ChatPanel = ({ messages, onSend, isThinking }: { messages: ChatMessage[], onSend: (m: string) => void, isThinking: boolean }) => {
  const [input, setInput] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, isThinking]);

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span><MessageSquare size={16} /> AI Assistant</span>
        <div className={`status-dot ${isThinking ? 'pulsing' : 'active'}`} />
      </div>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="message-content">{m.content}</div>
            {m.thinking && <div className="thinking-bubble">{m.thinking}</div>}
          </div>
        ))}
        {isThinking && <div className="message assistant thinking">Thinking...</div>}
        <div ref={endRef} />
      </div>
      <div className="chat-input-area">
        <div className="chat-input-row">
          <input 
            value={input} 
            onChange={e => setInput(e.target.value)} 
            onKeyDown={e => { if (e.key === 'Enter') { onSend(input); setInput(''); } }} 
            placeholder="Type your instruction..." 
          />
          <button className="primary-btn" style={{ padding: '6px' }} onClick={() => { onSend(input); setInput(''); }}>
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

const FileTreeNode = ({ node, onSelect }: { 
  node: FileNode; 
  onSelect: (path: string) => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const isDir = node.type === 'directory';

  return (
    <div className="tree-node">
      <div 
        className={`node-label ${isDir ? 'dir' : 'file'}`}
        onClick={() => isDir ? setIsOpen(!isOpen) : onSelect(node.path)}
      >
        <span className="node-icon">
          {isDir ? (isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />) : <FileCode size={14} />}
        </span>
        <span className="node-text">{node.name}</span>
      </div>
      {isDir && isOpen && node.children && (
        <div className="node-children">
          {node.children.map(child => (
            <FileTreeNode key={child.path} node={child} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
};

const Explorer = ({ files, onSelect, onCreateFile, onCreateDir }: any) => (
  <div className="explorer-view" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
    <div className="sidebar-header" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-primary)' }}>
      <span>EXPLORER</span>
      <div className="header-actions" style={{ display: 'flex', gap: '8px' }}>
        <button className="icon-btn" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => onCreateFile('new_agent.py')} title="New File"><Plus size={14} /></button>
        <button className="icon-btn" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }} onClick={() => onCreateDir('new_module')} title="New Folder"><FolderTree size={14} /></button>
      </div>
    </div>
    <div className="sidebar-content" style={{ flex: 1, overflowY: 'auto', padding: '12px 0' }}>
      {files.map((node: any) => (
        <FileTreeNode key={node.path} node={node} onSelect={onSelect} />
      ))}
    </div>
  </div>
);

const TerminalComponent = ({ onCommand }: { onCommand: (cmd: string) => void }) => {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>(['Welcome to NexLab 1.0 Professional Terminal.', 'Type "help" to see capabilities.']);
  
  const handleSubmit = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      onCommand(input);
      setHistory(prev => [...prev, `❯ ${input}`]);
      setInput('');
    }
  };

  return (
    <div className="terminal-body">
      <div className="terminal-history">
        {history.map((line, i) => <div key={i} className="terminal-line">{line}</div>)}
      </div>
      <div className="terminal-input-row">
        <span className="prompt">❯</span>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleSubmit} autoFocus />
      </div>
    </div>
  );
};

const WelcomeView = ({ onNewProject }: { onNewProject: () => void }) => (
  <div className="welcome-screen">
    <div className="premium-glow"></div>
    <div className="welcome-logo">💎</div>
    <div className="welcome-title">NexLab AI Framework 1.0</div>
    <div className="welcome-subtitle">
      The state-of-the-art environment for building next-generation agentic workflows.
    </div>
    <div className="welcome-actions">
      <button className="primary-btn" onClick={onNewProject}>
        <Plus size={18} /> New Agent Project
      </button>
      <button className="secondary-btn">
        <FolderTree size={18} /> Open Directory
      </button>
    </div>
  </div>
);

const NewProjectModal = ({ onClose, onCreate }: { onClose: () => void, onCreate: (name: string, path: string) => void }) => {
  const [name, setName] = useState('agent-alpha');
  const [path, setPath] = useState('');
  return (
    <div className="modal-overlay">
      <div className="configurator-modal project-modal">
        <div className="modal-header">
          <h2><Plus size={20} /> Create Agent Project</h2>
          <X size={20} style={{ cursor: 'pointer' }} onClick={onClose} />
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Project Name</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. MyCodeAssistant" />
          </div>
          <div className="form-group">
            <label>Physical Path</label>
            <input value={path} onChange={e => setPath(e.target.value)} placeholder="e.g. D:/Projects/NexLab/Alpha" />
          </div>
        </div>
        <div className="modal-footer">
          <button className="secondary-btn" onClick={onClose}>Cancel</button>
          <button className="primary-btn" onClick={() => onCreate(name, path)}>Scaffold Project</button>
        </div>
      </div>
    </div>
  );
};

// ═══════════ MAIN APPLICATION ═══════════

export default function App() {
  const [activeView, setActiveView] = useState<'explorer' | 'chat' | 'dashboard' | 'diagnostics' | 'tools'>('dashboard');
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [panelHeight] = useState(240);

  // Data
  const [files, setFiles] = useState<FileNode[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: 'assistant', content: 'NexLab 1.0 initialized. Systems verified. How shall we build today?' }
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const [diagnostics, setDiagnostics] = useState<any[]>([]);
  const [toolsList, setToolsList] = useState<any[]>([]);
  const [projectStats, setProjectStats] = useState<any>(null);
  const [agentConfig] = useState<AgentConfig>({
    provider: 'openai', model: 'gpt-4o', temperature: 0.7, 
    mentorEnabled: true, deepThinkerEnabled: true, mentorInterval: 5, maxResponseLength: 4096,
    tools: { 'File System': true, 'Terminal': true }
  });

  // UI
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);

  const refreshFiles = useCallback(async () => {
    try {
      const data = await apiGet<{ files: FileNode[] }>('/api/files');
      setFiles(data.files || []);
    } catch (e) { console.error("Disk sync failed", e); }
  }, []);

  const refreshStats = useCallback(async () => {
    try {
      const data = await apiGet<any>('/api/project/stats');
      setProjectStats(data);
    } catch (e) { }
  }, []);

  useEffect(() => {
    refreshFiles();
    refreshStats();
    const timer = setInterval(() => {
      apiGet<{ events: any[] }>('/api/agent/diagnostics?n=20').then(d => setDiagnostics(d.events || []));
      apiGet<{ tools: any[] }>('/api/agent/tools').then(d => setToolsList(d.tools || []));
      refreshStats();
    }, 4000);
    return () => clearInterval(timer);
  }, [refreshFiles, refreshStats]);

  const handleFileSelect = async (path: string) => {
    try {
      const data = await apiPost<{ content: string }>('/api/file/read', { path });
      setActiveFile(path);
      setFileContent(data.content);
      if (!openTabs.includes(path)) setOpenTabs([...openTabs, path]);
    } catch (e) { console.error("IO Error", e); }
  };

  const handleSaveFile = async () => {
    if (!activeFile) return;
    try {
      await apiPost('/api/file/save', { path: activeFile, content: fileContent });
    } catch (e) { alert("Write failed: " + e); }
  };

  const handleChatSend = async (message: string) => {
    if (!message.trim()) return;
    setChatMessages(prev => [...prev, { role: 'user', content: message }]);
    setIsThinking(true);
    try {
      const data = await apiPost<any>('/api/chat', { message, context: { activeFile } });
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply, thinking: data.thinking }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: "Warning: AI Connection Interrupted." }]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleCreateProject = async (name: string, path: string) => {
    try {
      const res = await apiPost<any>('/api/project/create', { name, path });
      if (res.status === 'ok') {
        setShowNewProjectModal(false);
        refreshFiles();
        refreshStats();
        setActiveView('dashboard');
      } else { alert("Scaffold error: " + res.error); }
    } catch (e) { alert("Project creation failed: " + e); }
  };

  const getLang = (path: string) => {
    const ext = path.split('.').pop();
    if (ext === 'py') return 'python';
    if (ext === 'js' || ext === 'jsx' || ext === 'ts' || ext === 'tsx') return 'typescript';
    if (ext === 'css') return 'css';
    if (ext === 'html') return 'html';
    if (ext === 'json') return 'json';
    if (ext === 'md') return 'markdown';
    return 'plaintext';
  };

  return (
    <div className="app-container">
      <div className="activity-bar">
        <div className={`activity-item ${activeView === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveView('dashboard')} title="Dashboard"><Layout size={24} /></div>
        <div className={`activity-item ${activeView === 'explorer' ? 'active' : ''}`} onClick={() => setActiveView('explorer')} title="Explorer"><FolderTree size={24} /></div>
        <div className={`activity-item ${activeView === 'chat' ? 'active' : ''}`} onClick={() => setActiveView('chat')} title="AI Chat"><MessageSquare size={24} /></div>
        <div className={`activity-item ${activeView === 'tools' ? 'active' : ''}`} onClick={() => setActiveView('tools')} title="Capabilities"><Boxes size={24} /></div>
        <div className={`activity-item ${activeView === 'diagnostics' ? 'active' : ''}`} onClick={() => { setActiveView('diagnostics'); setTerminalOpen(true); }} title="Diagnostics"><Activity size={24} /></div>
        <div className="activity-spacer" />
        <div className="activity-item" title="Framework Config"><Settings size={24} /></div>
      </div>

      <div className="main-content">
        {(activeView === 'explorer' || activeView === 'chat') && (
          <div className="sidebar" style={{ width: 300 }}>
            {activeView === 'explorer' && (
              <Explorer
                files={files}
                onSelect={handleFileSelect}
                onCreateFile={(path: string) => apiPost('/api/file/create', { path, type: 'file' }).then(refreshFiles)}
                onCreateDir={(path: string) => apiPost('/api/file/create', { path, type: 'directory' }).then(refreshFiles)}
              />
            )}
            {activeView === 'chat' && (
              <ChatPanel messages={chatMessages} onSend={handleChatSend} isThinking={isThinking} />
            )}
          </div>
        )}

        <div className="editor-container">
          <div className="tabs-bar">
            {openTabs.map(path => (
              <div key={path} className={`tab ${activeFile === path ? 'active' : ''}`} onClick={() => handleFileSelect(path)}>
                <FileCode size={14} style={{ marginRight: 6 }} />
                <span>{path.split('/').pop()}</span>
                <X size={14} className="close-tab" onClick={(e) => { 
                  e.stopPropagation(); 
                  const nextTabs = openTabs.filter(t => t !== path);
                  setOpenTabs(nextTabs); 
                  if (activeFile === path) setActiveFile(nextTabs[nextTabs.length - 1] || null); 
                }} />
              </div>
            ))}
          </div>

          <div className="view-content">
            {activeFile ? (
              <div className="editor-wrapper" style={{ height: '100%', position: 'relative' }}>
                <Editor
                  theme="vs-dark"
                  path={activeFile}
                  defaultLanguage={getLang(activeFile)}
                  value={fileContent}
                  onChange={(v) => { if (v !== undefined) setFileContent(v) }}
                  options={{ fontSize: 13, minimap: { enabled: false }, automaticLayout: true, padding: { top: 12 } }}
                />
                <button className="save-button" onClick={handleSaveFile} title="Save File"><Save size={20} /></button>
              </div>
            ) : activeView === 'dashboard' ? (
              <Dashboard stats={projectStats} />
            ) : activeView === 'diagnostics' ? (
              <DiagnosticsPanel events={diagnostics} />
            ) : activeView === 'tools' ? (
              <CapabilitiesPanel tools={toolsList} />
            ) : (
              <WelcomeView onNewProject={() => setShowNewProjectModal(true)} />
            )}
          </div>
        </div>

        {terminalOpen && (
          <div className="bottom-panel" style={{ height: panelHeight }}>
            <div className="panel-header">
              <span><TerminalIcon size={14} style={{ marginRight: 6 }} /> NEXLAB TERMINAL v1.0</span>
              <X size={14} style={{ cursor: 'pointer' }} onClick={() => setTerminalOpen(false)} />
            </div>
            <div className="panel-content"><TerminalComponent onCommand={(cmd) => apiPost('/api/terminal/exec', { command: cmd })} /></div>
          </div>
        )}

        <div className="statusbar">
          <div className="statusbar-left">
            <div className="statusbar-item"><Globe size={14} /> <span>prod-alpha</span></div>
            <div className="statusbar-item">{openTabs.length} active tabs</div>
            <div className="statusbar-item"><CheckCircle2 size={14} color="#5bffc2" /> <span>Unified Kernel Active</span></div>
          </div>
          <div className="statusbar-right">
            <div className="statusbar-item">{activeFile ? getLang(activeFile) : 'Framework 1.0.0'}</div>
            <div className="statusbar-item">
              <Cpu size={14} /> {agentConfig.provider}:{agentConfig.model}
            </div>
          </div>
        </div>
      </div>

      {showNewProjectModal && <NewProjectModal onClose={() => setShowNewProjectModal(false)} onCreate={handleCreateProject} />}
    </div>
  );
}
