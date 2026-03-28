import { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Brain, Zap, Database, ShieldCheck, HardDrive, Play, X, Square } from 'lucide-react';
import SmartNode from './SmartNode';

const nodeTypes: NodeTypes = {
  smart: SmartNode as any,
};

const initialNodes = [
  { 
    id: '1', 
    type: 'smart', 
    position: { x: 250, y: 50 }, 
    data: { label: 'Model Source (OpenRouter)', type: 'source', status: 'idle' } 
  },
  { 
    id: '2', 
    type: 'smart', 
    position: { x: 250, y: 200 }, 
    data: { label: 'Swarm Coder Agent', type: 'agent', status: 'idle' } 
  },
  { 
    id: '3', 
    type: 'smart', 
    position: { x: 550, y: 200 }, 
    data: { label: 'Docker Sandbox Exec', type: 'sandbox', status: 'idle' } 
  },
  { 
    id: '4', 
    type: 'smart', 
    position: { x: 550, y: 50 }, 
    data: { label: 'Tester Agent', type: 'agent', status: 'idle' } 
  }
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
  { id: 'e2-3', source: '2', target: '3' },
  { id: 'e3-4', source: '3', target: '4' },
  { id: 'e4-2', source: '4', target: '2', label: 'Feedback Loop', animated: true }
];

let id = 5;
const getId = () => `${id++}`;

const FlowInternal = ({ onClose }: { onClose: () => void }) => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes as any);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<{ id: string, label: string, msg: string }[]>([]);
  const { screenToFlowPosition } = useReactFlow();

  const onConnect = useCallback((params: any) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const addLog = (label: string, msg: string) => {
    setLogs(prev => [{ id: Math.random().toString(), label, msg }, ...prev].slice(0, 50));
  };

  const updateNodeStatus = (nodeId: string, status: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, status } };
        }
        return node;
      })
    );
  };

  const executePipeline = async () => {
    if (running) return;
    setRunning(true);
    addLog("SYSTEM", "Initializing Swarm Pipeline v1.3...");

    // Sequence simulation
    const sequence = [
      { id: '1', msg: "Fetching model parameters from OpenRouter (gemma-3-4b)..." },
      { id: '2', msg: "CoderAgent: Analyzing codebase and generating solution..." },
      { id: '3', msg: "Sandbox: Executing code in isolated Docker environment..." },
      { id: '4', msg: "Tester: Validating outputs and edge cases..." },
    ];

    for (const step of sequence) {
      updateNodeStatus(step.id, 'running');
      addLog("AGENT", step.msg);
      await new Promise(r => setTimeout(r, 1500));
      updateNodeStatus(step.id, 'success');
    }

    addLog("SYSTEM", "Pipeline Execution Successfully Completed.");
    setRunning(false);
  };

  const onDragOver = useCallback((event: any) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: any) => {
      event.preventDefault();

      const typeStr = event.dataTransfer.getData('application/reactflow');
      if (typeof typeStr === 'undefined' || !typeStr) return;
      const [type, label] = typeStr.split(':');

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: getId(),
        type: 'smart',
        position,
        data: { label, type, status: 'idle' },
      };

      setNodes((nds) => nds.concat(newNode as any));
    },
    [screenToFlowPosition, setNodes]
  );

  return (
    <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
      
      {/* Sidebar: Library */}
      <div className="node-editor-sidebar">
        <div style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-dim)', marginBottom: '8px' }}>NODE LIBRARY</div>
        
        <div className="library-node" draggable onDragStart={(e: any) => e.dataTransfer.setData('application/reactflow', 'agent:New Intelligent Agent')}>
          <Brain size={16} color="var(--accent-base)" /> <span>Agent Node</span>
        </div>
        <div className="library-node" draggable onDragStart={(e: any) => e.dataTransfer.setData('application/reactflow', 'tool:PostgreSQL Tool')}>
          <Zap size={16} color="var(--warning)" /> <span>Tool Node</span>
        </div>
        <div className="library-node" draggable onDragStart={(e: any) => e.dataTransfer.setData('application/reactflow', 'source:S3 Bucket')}>
          <Database size={16} color="var(--success)" /> <span>Data Source</span>
        </div>
        <div className="library-node" draggable onDragStart={(e: any) => e.dataTransfer.setData('application/reactflow', 'sandbox:Docker Sandbox')}>
          <ShieldCheck size={16} color="#38bdf8" /> <span>Sandbox</span>
        </div>
        <div className="library-node" draggable onDragStart={(e: any) => e.dataTransfer.setData('application/reactflow', 'memory:Vector DB')}>
          <HardDrive size={16} color="#a78bfa" /> <span>Memory</span>
        </div>

        <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-muted)' }}>
          <button className="btn btn-primary" style={{ width: '100%', gap: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={executePipeline} disabled={running}>
            {running ? <Square size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" />}
            {running ? 'Stop Task' : 'Run Pipeline'}
          </button>
        </div>
      </div>

      {/* Main Flow Canvas */}
      <div style={{ flex: 1, height: '100%', position: 'relative' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          colorMode="dark"
          fitView
        >
          <Controls />
          <MiniMap nodeStrokeWidth={3} zoomable pannable />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>

        {/* Output Console Window */}
        <div className="studio-console">
          <div className="console-header">
            AI Intelligence Stream
          </div>
          <div className="console-content">
            {logs.length === 0 && <div style={{ opacity: 0.3, fontStyle: 'italic' }}>Waiting for pipeline execution...</div>}
            {logs.map((log) => (
              <div key={log.id} className="console-msg">
                <span className="console-label">[{log.label}]</span>
                <span>{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Close Button UI */}
      <button 
        onClick={onClose}
        style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 1002, background: 'var(--bg-elevated)', border: '1px solid var(--border-active)', width: '36px', height: '36px', borderRadius: '18px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
      >
        <X size={20} />
      </button>
    </div>
  );
};

const NodeEditor = ({ isVisible, onClose }: { isVisible: boolean, onClose: () => void }) => {
  if (!isVisible) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'var(--bg-base)', zIndex: 1000, display: 'flex'
    }}>
      <ReactFlowProvider>
        <FlowInternal onClose={onClose} />
      </ReactFlowProvider>
    </div>
  );
};

export default NodeEditor;
