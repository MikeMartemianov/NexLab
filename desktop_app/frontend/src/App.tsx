import { useState, useRef, useEffect, useCallback } from 'react'
import Editor from '@monaco-editor/react'
import './index.css'

// ═══════════ TYPES ═══════════
interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  children?: FileNode[]
  expanded?: boolean
}

interface ChatMessage {
  id: number
  role: 'user' | 'ai'
  content: string
  thinking?: string
}

interface AgentConfig {
  provider: string
  model: string
  temperature: number
  mentorEnabled: boolean
  deepThinkerEnabled: boolean
  mentorInterval: number
  maxResponseLength: number
  tools: Record<string, boolean>
}

// ═══════════ FILE ICONS ═══════════
function getFileIcon(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  const icons: Record<string, string> = {
    py: '🐍', js: '🟨', ts: '🔷', tsx: '⚛️', jsx: '⚛️',
    json: '📋', yaml: '⚙️', yml: '⚙️', md: '📝', css: '🎨',
    html: '🌐', txt: '📄', toml: '🔧', cfg: '🔧', sh: '⬛',
    bat: '⬛', ps1: '⬛', png: '🖼️', jpg: '🖼️', svg: '🖼️',
    git: '🔀', lock: '🔒',
  }
  return icons[ext] || '📄'
}

function getLanguage(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || ''
  const langs: Record<string, string> = {
    py: 'python', js: 'javascript', ts: 'typescript', tsx: 'typescriptreact',
    jsx: 'javascriptreact', json: 'json', yaml: 'yaml', yml: 'yaml',
    md: 'markdown', css: 'css', html: 'html', toml: 'toml',
    sh: 'shell', bat: 'bat', ps1: 'powershell', xml: 'xml',
    sql: 'sql', rs: 'rust', go: 'go', java: 'java', cpp: 'cpp',
    c: 'c', h: 'c', txt: 'plaintext',
  }
  return langs[ext] || 'plaintext'
}

// ═══════════ BACKEND API ═══════════
const API = 'http://127.0.0.1:8000'

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  return res.json()
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return res.json()
}

// ═══════════ FILE TREE COMPONENT ═══════════
function FileTree({ files, activeFile, onFileClick, onRefresh, onContextMenu }: {
  files: FileNode[]
  activeFile: string | null
  onFileClick: (f: FileNode) => void
  onRefresh: () => void
  onContextMenu: (e: React.MouseEvent, f: FileNode) => void
}) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggle = (path: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(path) ? next.delete(path) : next.add(path)
      return next
    })
  }

  const renderNode = (node: FileNode, depth: number): React.ReactNode => (
    <div key={node.path}>
      <div
        className={`tree-item ${activeFile === node.path ? 'active' : ''}`}
        style={{ paddingLeft: 12 + depth * 16 }}
        onClick={() => node.type === 'directory' ? toggle(node.path) : onFileClick(node)}
        onContextMenu={(e) => { e.preventDefault(); onContextMenu(e, node) }}
      >
        <span className="icon">
          {node.type === 'directory'
            ? (expanded.has(node.path) ? '📂' : '📁')
            : getFileIcon(node.name)
          }
        </span>
        {node.name}
      </div>
      {node.type === 'directory' && expanded.has(node.path) && node.children?.map(c => renderNode(c, depth + 1))}
    </div>
  )

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span>Explorer</span>
        <div className="sidebar-actions">
          <button className="sidebar-btn" onClick={onRefresh} title="Refresh">🔄</button>
        </div>
      </div>
      <div className="file-tree">
        {files.map(f => renderNode(f, 0))}
      </div>
    </div>
  )
}

// ═══════════ CHAT COMPONENT ═══════════
function ChatPanel({ messages, onSend, isThinking }: {
  messages: ChatMessage[]
  onSend: (msg: string) => void
  isThinking: boolean
}) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isThinking])

  const handleSend = () => {
    if (!input.trim()) return
    onSend(input.trim())
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span style={{ fontSize: 18 }}>✨</span>
        <span className="chat-header-title">NexLab AI Assistant</span>
        <div className="chat-status">
          <div className="chat-status-dot" />
          Online
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
            <div style={{ fontSize: 14 }}>Hi! I'm your AI assistant.</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>Ask me to write code, explain concepts, or help with your project.</div>
          </div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`chat-message ${msg.role}`}>
            {msg.thinking && (
              <div className="chat-thinking">
                💭 {msg.thinking}
              </div>
            )}
            <div className="chat-bubble">
              {msg.content.split('\n').map((line, i) => (
                <span key={i}>{line}{i < msg.content.split('\n').length - 1 && <br />}</span>
              ))}
            </div>
          </div>
        ))}
        {isThinking && (
          <div className="chat-message ai">
            <div className="chat-thinking">
              <div className="thinking-dots">
                <span /><span /><span />
              </div>
              AI is thinking deeply...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Ask AI anything... (Shift+Enter for newline)"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  )
}

// ═══════════ AGENT CONFIGURATOR MODAL ═══════════
function AgentConfigurator({ config, onChange, onClose, onSave }: {
  config: AgentConfig
  onChange: (c: AgentConfig) => void
  onClose: () => void
  onSave: () => void
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-title">🤖 Agent Studio</div>

        <div className="config-group">
          <div className="config-label">Model Provider</div>
          <select
            className="config-select"
            value={config.provider}
            onChange={e => onChange({ ...config, provider: e.target.value })}
          >
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama (Local)</option>
            <option value="anthropic">Anthropic</option>
            <option value="custom">Custom Python Module</option>
          </select>
        </div>

        <div className="config-group">
          <div className="config-label">Model Name</div>
          <input
            className="config-input"
            value={config.model}
            onChange={e => onChange({ ...config, model: e.target.value })}
            placeholder="e.g. gpt-4o, llama3, claude-3..."
          />
        </div>

        <div className="config-group">
          <div className="config-label">Temperature</div>
          <div className="config-slider-row">
            <input
              type="range"
              className="config-slider"
              min={0} max={2} step={0.05}
              value={config.temperature}
              onChange={e => onChange({ ...config, temperature: parseFloat(e.target.value) })}
            />
            <span className="config-slider-value">{config.temperature.toFixed(2)}</span>
          </div>
        </div>

        <div className="config-group">
          <div className="config-label">Max Response Length</div>
          <div className="config-slider-row">
            <input
              type="range"
              className="config-slider"
              min={256} max={16384} step={256}
              value={config.maxResponseLength}
              onChange={e => onChange({ ...config, maxResponseLength: parseInt(e.target.value) })}
            />
            <span className="config-slider-value">{config.maxResponseLength}</span>
          </div>
        </div>

        <div className="config-group">
          <div className="config-label">Mentor AI Interval (sec)</div>
          <div className="config-slider-row">
            <input
              type="range"
              className="config-slider"
              min={1} max={60} step={1}
              value={config.mentorInterval}
              onChange={e => onChange({ ...config, mentorInterval: parseInt(e.target.value) })}
            />
            <span className="config-slider-value">{config.mentorInterval}s</span>
          </div>
        </div>

        <div className="config-group">
          <div className="config-label">Components</div>
          <div className="config-toggle-row">
            <span className="config-toggle-label">Mentor AI (Nastavnik)</span>
            <div
              className={`toggle-switch ${config.mentorEnabled ? 'active' : ''}`}
              onClick={() => onChange({ ...config, mentorEnabled: !config.mentorEnabled })}
            />
          </div>
          <div className="config-toggle-row">
            <span className="config-toggle-label">Deep Thinker AI</span>
            <div
              className={`toggle-switch ${config.deepThinkerEnabled ? 'active' : ''}`}
              onClick={() => onChange({ ...config, deepThinkerEnabled: !config.deepThinkerEnabled })}
            />
          </div>
        </div>

        <div className="config-group">
          <div className="config-label">Available Tools</div>
          {Object.entries(config.tools).map(([tool, enabled]) => (
            <div className="config-toggle-row" key={tool}>
              <span className="config-toggle-label">{tool}</span>
              <div
                className={`toggle-switch ${enabled ? 'active' : ''}`}
                onClick={() => onChange({
                  ...config,
                  tools: { ...config.tools, [tool]: !enabled }
                })}
              />
            </div>
          ))}
        </div>

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={onSave}>💾 Save & Apply</button>
        </div>
      </div>
    </div>
  )
}

// ═══════════ CONTEXT MENU ═══════════
function ContextMenu({ x, y, node, onClose, onAction }: {
  x: number; y: number
  node: FileNode
  onClose: () => void
  onAction: (action: string, node: FileNode) => void
}) {
  useEffect(() => {
    const handler = () => onClose()
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [onClose])

  return (
    <div className="context-menu" style={{ top: y, left: x }}>
      {node.type === 'directory' && (
        <>
          <div className="context-menu-item" onClick={() => onAction('new_file', node)}>📄 New File</div>
          <div className="context-menu-item" onClick={() => onAction('new_folder', node)}>📁 New Folder</div>
          <div className="context-menu-divider" />
        </>
      )}
      <div className="context-menu-item" onClick={() => onAction('rename', node)}>✏️ Rename</div>
      <div className="context-menu-item" onClick={() => onAction('delete', node)}>🗑️ Delete</div>
    </div>
  )
}

// ═══════════ MAIN APP ═══════════
const DEFAULT_AGENT_CONFIG: AgentConfig = {
  provider: 'ollama',
  model: 'llama3',
  temperature: 0.7,
  mentorEnabled: true,
  deepThinkerEnabled: true,
  mentorInterval: 5,
  maxResponseLength: 4096,
  tools: {
    'File System': true,
    'Terminal Commands': true,
    'Web Search': false,
    'Code Analysis': true,
    'Image Generation': false,
  },
}

export default function App() {
  // Layout state
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(true)
  const [panelOpen, setPanelOpen] = useState(false)
  const [panelHeight] = useState(240)

  // File system state
  const [files, setFiles] = useState<FileNode[]>([])
  const [openTabs, setOpenTabs] = useState<{ path: string; name: string; content: string; modified: boolean }[]>([])
  const [activeTab, setActiveTab] = useState<string | null>(null)

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [nextMsgId, setNextMsgId] = useState(1)

  // Agent config
  const [showConfigurator, setShowConfigurator] = useState(false)
  const [agentConfig, setAgentConfig] = useState<AgentConfig>(DEFAULT_AGENT_CONFIG)

  // Context menu
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; node: FileNode } | null>(null)

  // Terminal output
  const [terminalOutput, setTerminalOutput] = useState<string[]>([
    '> NexLab AI Code Editor v1.0',
    '> Type commands here...',
    '',
  ])
  const [terminalInput, setTerminalInput] = useState('')

  // Load file tree
  const loadFiles = useCallback(async () => {
    try {
      const data = await apiGet<{ files: FileNode[] }>('/api/files')
      setFiles(data.files || [])
    } catch {
      // Backend not available yet, use demo data
      setFiles([
        {
          name: 'src', path: '/src', type: 'directory', children: [
            { name: 'main.py', path: '/src/main.py', type: 'file' },
            { name: 'utils.py', path: '/src/utils.py', type: 'file' },
            {
              name: 'components', path: '/src/components', type: 'directory', children: [
                { name: 'agent.py', path: '/src/components/agent.py', type: 'file' },
              ]
            },
          ]
        },
        { name: 'README.md', path: '/README.md', type: 'file' },
        { name: 'pyproject.toml', path: '/pyproject.toml', type: 'file' },
      ])
    }
  }, [])

  useEffect(() => { loadFiles() }, [loadFiles])

  // Open a file
  const openFile = async (node: FileNode) => {
    if (openTabs.find(t => t.path === node.path)) {
      setActiveTab(node.path)
      return
    }

    let content = ''
    try {
      const data = await apiGet<{ content: string }>(`/api/file?path=${encodeURIComponent(node.path)}`)
      content = data.content || ''
    } catch {
      content = `# ${node.name}\n\n# File content will be loaded from the backend.`
    }

    setOpenTabs(prev => [...prev, { path: node.path, name: node.name, content, modified: false }])
    setActiveTab(node.path)
  }

  // Close a tab
  const closeTab = (path: string) => {
    setOpenTabs(prev => {
      const next = prev.filter(t => t.path !== path)
      if (activeTab === path) {
        setActiveTab(next.length > 0 ? next[next.length - 1].path : null)
      }
      return next
    })
  }

  // Editor content change
  const handleEditorChange = (value: string | undefined) => {
    if (!activeTab || value === undefined) return
    setOpenTabs(prev =>
      prev.map(t => t.path === activeTab ? { ...t, content: value, modified: true } : t)
    )
  }

  // Save file
  const saveFile = async () => {
    const tab = openTabs.find(t => t.path === activeTab)
    if (!tab) return
    try {
      await apiPost('/api/file/save', { path: tab.path, content: tab.content })
      setOpenTabs(prev => prev.map(t => t.path === activeTab ? { ...t, modified: false } : t))
    } catch {
      // Silently fail if backend not available
    }
  }

  // Chat send
  const handleChatSend = async (msg: string) => {
    const userMsg: ChatMessage = { id: nextMsgId, role: 'user', content: msg }
    setChatMessages(prev => [...prev, userMsg])
    setNextMsgId(prev => prev + 1)
    setIsThinking(true)

    try {
      const data = await apiPost<{ reply: string; thinking?: string }>('/api/chat', {
        message: msg,
        context: {
          activeFile: activeTab,
          openFiles: openTabs.map(t => t.path),
        }
      })

      const aiMsg: ChatMessage = {
        id: nextMsgId + 1,
        role: 'ai',
        content: data.reply || 'I understood your request. Let me help you with that.',
        thinking: data.thinking,
      }
      setChatMessages(prev => [...prev, aiMsg])
      setNextMsgId(prev => prev + 2)
    } catch {
      const errorMsg: ChatMessage = {
        id: nextMsgId + 1,
        role: 'ai',
        content: '⚠️ Backend is not connected. Start the server with `python desktop_app/app.py` to enable AI features.',
      }
      setChatMessages(prev => [...prev, errorMsg])
      setNextMsgId(prev => prev + 2)
    }

    setIsThinking(false)
  }

  // Context menu actions
  const handleContextAction = async (action: string, node: FileNode) => {
    setCtxMenu(null)
    if (action === 'new_file') {
      const name = prompt('New file name:')
      if (name) {
        try { await apiPost('/api/file/create', { path: `${node.path}/${name}`, type: 'file' }) } catch { }
        loadFiles()
      }
    } else if (action === 'new_folder') {
      const name = prompt('New folder name:')
      if (name) {
        try { await apiPost('/api/file/create', { path: `${node.path}/${name}`, type: 'directory' }) } catch { }
        loadFiles()
      }
    } else if (action === 'delete') {
      if (confirm(`Delete "${node.name}"?`)) {
        try { await apiPost('/api/file/delete', { path: node.path }) } catch { }
        loadFiles()
      }
    } else if (action === 'rename') {
      const name = prompt('New name:', node.name)
      if (name && name !== node.name) {
        try { await apiPost('/api/file/rename', { path: node.path, newName: name }) } catch { }
        loadFiles()
      }
    }
  }

  // Terminal
  const handleTerminalSubmit = async (e: React.KeyboardEvent) => {
    if (e.key !== 'Enter') return
    const cmd = terminalInput.trim()
    if (!cmd) return
    setTerminalOutput(prev => [...prev, `$ ${cmd}`])
    setTerminalInput('')
    try {
      const data = await apiPost<{ output: string }>('/api/terminal/exec', { command: cmd })
      setTerminalOutput(prev => [...prev, data.output || ''])
    } catch {
      setTerminalOutput(prev => [...prev, '[Terminal not connected to backend]'])
    }
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 's') { e.preventDefault(); saveFile() }
      if (e.ctrlKey && e.key === 'b') { e.preventDefault(); setSidebarOpen(p => !p) }
      if (e.ctrlKey && e.key === 'j') { e.preventDefault(); setPanelOpen(p => !p) }
      if (e.ctrlKey && e.key === 'l') { e.preventDefault(); setChatOpen(p => !p) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })

  const activeTabData = openTabs.find(t => t.path === activeTab)

  const layoutClasses = [
    'app-layout',
    !sidebarOpen && 'sidebar-collapsed',
    !chatOpen && 'chat-collapsed',
  ].filter(Boolean).join(' ')

  return (
    <>
      <div className={layoutClasses}>
        {/* HEADER */}
        <div className="header">
          <div className="header-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
            NexLab
          </div>

          <div className="header-actions">
            <button
              className={`header-btn ${sidebarOpen ? 'active' : ''}`}
              onClick={() => setSidebarOpen(p => !p)}
              title="Toggle Explorer (Ctrl+B)"
            >📁</button>
            <button
              className={`header-btn ${panelOpen ? 'active' : ''}`}
              onClick={() => setPanelOpen(p => !p)}
              title="Toggle Terminal (Ctrl+J)"
            >⬛</button>
            <button
              className="header-btn"
              onClick={() => setShowConfigurator(true)}
              title="Agent Studio"
            >🤖</button>
            <button
              className={`header-btn ${chatOpen ? 'active' : ''}`}
              onClick={() => setChatOpen(p => !p)}
              title="Toggle AI Chat (Ctrl+L)"
            >✨</button>
          </div>
        </div>

        {/* SIDEBAR */}
        {sidebarOpen && (
          <FileTree
            files={files}
            activeFile={activeTab}
            onFileClick={openFile}
            onRefresh={loadFiles}
            onContextMenu={(e, f) => setCtxMenu({ x: e.clientX, y: e.clientY, node: f })}
          />
        )}

        {/* EDITOR AREA */}
        <div className="editor-area" style={!sidebarOpen ? { gridColumn: sidebarOpen ? '2' : '1 / 3' } : undefined}>
          {/* Tab bar */}
          <div className="tab-bar">
            {openTabs.map(tab => (
              <div
                key={tab.path}
                className={`tab ${activeTab === tab.path ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.path)}
              >
                <span className="tab-icon">{getFileIcon(tab.name)}</span>
                {tab.name}
                {tab.modified && <span style={{ color: 'var(--status-warning)', marginLeft: 4 }}>●</span>}
                <button className="tab-close" onClick={(e) => { e.stopPropagation(); closeTab(tab.path) }}>✕</button>
              </div>
            ))}
          </div>

          {/* Editor or Welcome */}
          {activeTabData ? (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
              <div className="monaco-container" style={{ flex: panelOpen ? `1 1 calc(100% - ${panelHeight}px)` : '1' }}>
                <Editor
                  theme="vs-dark"
                  language={getLanguage(activeTabData.name)}
                  value={activeTabData.content}
                  onChange={handleEditorChange}
                  options={{
                    fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
                    fontSize: 14,
                    lineHeight: 22,
                    minimap: { enabled: true },
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    cursorSmoothCaretAnimation: 'on',
                    renderWhitespace: 'selection',
                    bracketPairColorization: { enabled: true },
                    padding: { top: 12 },
                    scrollBeyondLastLine: false,
                  }}
                />
              </div>

              {/* Bottom Panel (Terminal) */}
              {panelOpen && (
                <div className="bottom-panel" style={{ height: panelHeight }}>
                  <div className="panel-tabs">
                    <div className="panel-tab active">Terminal</div>
                    <div className="panel-tab">Problems</div>
                    <div className="panel-tab">Output</div>
                  </div>
                  <div className="terminal-container" style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: 12,
                    padding: '8px 12px',
                    overflowY: 'auto',
                    flex: 1,
                    background: 'var(--bg-primary)',
                  }}>
                    {terminalOutput.map((line, i) => (
                      <div key={i} style={{ color: line.startsWith('$') ? 'var(--accent-secondary)' : 'var(--text-secondary)' }}>
                        {line}
                      </div>
                    ))}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <span style={{ color: 'var(--accent-secondary)' }}>$</span>
                      <input
                        value={terminalInput}
                        onChange={e => setTerminalInput(e.target.value)}
                        onKeyDown={handleTerminalSubmit}
                        style={{
                          flex: 1,
                          border: 'none',
                          background: 'transparent',
                          color: 'var(--text-primary)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: 12,
                          outline: 'none',
                        }}
                        placeholder="Enter command..."
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="welcome-screen">
              <div className="welcome-logo">⚡</div>
              <div className="welcome-title">NexLab AI Code Editor</div>
              <div className="welcome-subtitle">
                A professional code editor with deep AI integration.
                Open a file from the explorer or chat with AI to get started.
              </div>
              <div className="welcome-shortcuts">
                <div className="shortcut-row">
                  <span className="shortcut-key">Ctrl+B</span>
                  <span>Toggle Explorer</span>
                </div>
                <div className="shortcut-row">
                  <span className="shortcut-key">Ctrl+L</span>
                  <span>Toggle AI Chat</span>
                </div>
                <div className="shortcut-row">
                  <span className="shortcut-key">Ctrl+J</span>
                  <span>Toggle Terminal</span>
                </div>
                <div className="shortcut-row">
                  <span className="shortcut-key">Ctrl+S</span>
                  <span>Save File</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* CHAT PANEL */}
        {chatOpen && (
          <ChatPanel
            messages={chatMessages}
            onSend={handleChatSend}
            isThinking={isThinking}
          />
        )}

        {/* STATUS BAR */}
        <div className="statusbar">
          <div className="statusbar-left">
            <div className="statusbar-item">🌿 main</div>
            <div className="statusbar-item">{openTabs.length} files open</div>
          </div>
          <div className="statusbar-right">
            <div className="statusbar-item">
              {activeTabData ? getLanguage(activeTabData.name) : 'No file'}
            </div>
            <div className="statusbar-item">UTF-8</div>
            <div className="statusbar-item" style={{ cursor: 'pointer' }} onClick={() => setShowConfigurator(true)}>
              🤖 {agentConfig.provider}/{agentConfig.model}
            </div>
          </div>
        </div>
      </div>

      {/* MODALS */}
      {showConfigurator && (
        <AgentConfigurator
          config={agentConfig}
          onChange={setAgentConfig}
          onClose={() => setShowConfigurator(false)}
          onSave={() => {
            setShowConfigurator(false)
            // Send config to backend
            apiPost('/api/agent/configure', agentConfig).catch(() => {})
          }}
        />
      )}

      {/* CONTEXT MENU */}
      {ctxMenu && (
        <ContextMenu
          x={ctxMenu.x}
          y={ctxMenu.y}
          node={ctxMenu.node}
          onClose={() => setCtxMenu(null)}
          onAction={handleContextAction}
        />
      )}
    </>
  )
}
