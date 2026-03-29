import { useState, useCallback, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Brain, Zap, Database, ShieldCheck, HardDrive, Play, Square, Terminal as TerminalIcon } from 'lucide-react';
import SmartNode from './SmartNode';
import { useAppStore } from '../store';

const nodeTypes = {
  smart: SmartNode as any,
};

const initialNodes = [
  { id: '1', type: 'smart', position: { x: 250, y: 50 }, data: { label: 'User Input / Trigger', type: 'source', status: 'idle' } },
  { id: '2', type: 'smart', position: { x: 250, y: 200 }, data: { label: 'Primary AI Brain', type: 'agent', status: 'idle' } },
  { id: '3', type: 'smart', position: { x: 550, y: 200 }, data: { label: 'Vector Memory', type: 'memory', status: 'idle' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
];

const FlowInternal = () => {
  const { setView, config } = useAppStore();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes as any);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<any[]>([]);
  const { screenToFlowPosition } = useReactFlow();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://127.0.0.1:8000/api/flow/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLogs(prev => [{ id: Math.random(), ...data }, ...prev].slice(0, 100));
      
      // Update node status based on real event
      setNodes((nds) => nds.map((n) => {
        if (n.id === data.node_id) {
          return { ...n, data: { ...n.data, status: data.status } };
        }
        return n;
      }));
    };
    socketRef.current = ws;
    return () => ws.close();
  }, [setNodes]);

  const onConnect = useCallback((params: any) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const executePipeline = async () => {
    if (running) return;
    setRunning(true);
    setLogs([]);
    
    await fetch('http://127.0.0.1:8000/api/flow/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nodes, edges })
    });

    setRunning(false);
  };

  const onDrop = useCallback((event: any) => {
    event.preventDefault();
    const typeStr = event.dataTransfer.getData('application/reactflow');
    if (!typeStr) return;
    const [type, label] = typeStr.split(':');
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    const newNode = { id: `node_${Date.now()}`, type: 'smart', position, data: { label, type, status: 'idle' } };
    setNodes((nds) => nds.concat(newNode as any));
  }, [screenToFlowPosition, setNodes]);

  return (
    <div className="flex h-screen w-screen bg-dark">
      {/* Sidebar Library */}
      <div className="w-56 border-r border-muted bg-surface flex flex-col p-4 gap-2">
        <div className="text-[10px] text-dim font-bold uppercase tracking-widest mb-2 px-2">Node Library</div>
        {[
          { icon: Brain, label: 'Intelligent Agent', type: 'agent' },
          { icon: Zap, label: 'External Tool', type: 'tool' },
          { icon: Database, label: 'Data Registry', type: 'source' },
          { icon: ShieldCheck, label: 'Secure Sandbox', type: 'sandbox' },
          { icon: HardDrive, label: 'Vector Memory', type: 'memory' }
        ].map((item) => (
          <div key={item.type} className="library-node flex items-center gap-3 p-3 rounded-xl cursor-grab bg-elevated/40 hover:bg-elevated border border-muted transition-all"
            draggable onDragStart={(e) => e.dataTransfer.setData('application/reactflow', `${item.type}:${item.label}`)}>
            <item.icon size={16} className="text-accent-base" />
            <span className="text-xs font-medium">{item.label}</span>
          </div>
        ))}
        
        <div className="mt-auto pt-4 border-t border-muted">
          <button className="btn btn-primary w-full flex items-center justify-center gap-2 py-3" onClick={executePipeline} disabled={running}>
            {running ? <Square size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" />}
            {running ? 'Halt Swarm' : 'Execute Flow'}
          </button>
          <button className="btn btn-secondary w-full mt-2 py-2 text-xs" onClick={() => setView('config-editor')}>
            Back to Config
          </button>
        </div>
      </div>

      {/* Editor & Console */}
      <div className="flex-1 flex flex-col relative">
        <div className="flex-1">
          <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} 
            onConnect={onConnect} onDrop={onDrop} onDragOver={(e) => e.preventDefault()} nodeTypes={nodeTypes} colorMode="dark" fitView>
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>

        {/* Console Terminal */}
        <div className="h-64 border-t border-muted bg-surface flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-bottom border-muted bg-base/50">
            <div className="flex items-center gap-2 text-xs font-bold text-accent-base">
              <TerminalIcon size={14} /> LIVE EXECUTION STREAM
            </div>
            <div className="text-[10px] text-dim">{config?.name || 'SmartAgent'} v{config?.version || '1.0'}</div>
          </div>
          <div className="flex-1 p-4 font-mono text-[11px] overflow-y-auto custom-scrollbar flex flex-col gap-1">
            {logs.length === 0 && <div className="text-dim italic opacity-50">Waiting for trigger event...</div>}
            {logs.map((log, i) => (
              <div key={log.id || i} className="flex gap-4 animate-in fade-in slide-in-from-left duration-300">
                 <span className="text-dim opacity-50">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                 <span className="text-accent-base font-bold">[{log.node_id}]</span>
                 <span className={`px-2 rounded ${log.status === 'error' ? 'bg-error/20 text-error' : 'bg-success/20 text-success'}`}>
                   {log.status.toUpperCase()}
                 </span>
                 <span className="text-main">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const NodeEditor = ({ isVisible }: { isVisible: boolean, onClose: () => void }) => {
  if (!isVisible) return null;
  return (
    <div className="fixed inset-0 z-[1000] flex">
      <ReactFlowProvider>
        <FlowInternal />
      </ReactFlowProvider>
    </div>
  );
};

export default NodeEditor;
