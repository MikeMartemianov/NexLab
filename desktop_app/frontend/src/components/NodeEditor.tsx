import React, { useState, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 100, y: 100 }, data: { label: 'Model Source (OpenRouter)' }, type: 'input' },
  { id: '2', position: { x: 100, y: 250 }, data: { label: 'Swarm Coder Agent' } },
  { id: '3', position: { x: 400, y: 250 }, data: { label: 'Docker Sandbox Exec' } },
  { id: '4', position: { x: 400, y: 100 }, data: { label: 'Tester Agent' } }
];
const initialEdges = [
  { id: 'e1-2', source: '1', target: '2' },
  { id: 'e2-3', source: '2', target: '3' },
  { id: 'e3-4', source: '3', target: '4' },
  { id: 'e4-2', source: '4', target: '2', label: 'Retry Loop' }
];

const NodeEditor = ({ isVisible, onClose }: { isVisible: boolean, onClose: () => void }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [running, setRunning] = useState(false);

  const onConnect = useCallback((params: any) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const executePipeline = async () => {
    setRunning(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/flow/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nodes, edges })
      });
      const data = await res.json();
      alert("Pipeline Execution Result: " + data.status);
    } catch (e) {
      alert("Error running pipeline. Check backend logs.");
    } finally {
      setRunning(false);
    }
  };

  if (!isVisible) return null;

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'var(--bg-base)', zIndex: 1000, display: 'flex', flexDirection: 'column'
    }}>
      <div style={{ padding: '16px', background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-muted)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>NexLab Agent Flow Studio</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn btn-primary" onClick={executePipeline} disabled={running}>
            {running ? 'Running...' : 'Execute Pipeline'}
          </button>
          <button className="btn btn-secondary" onClick={onClose}>Close Studio</button>
        </div>
      </div>
      <div style={{ flex: 1 }}>
        {/* We map default styles since reactflow variables can clash */}
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          colorMode="dark"
        >
          <Controls />
          <MiniMap nodeStrokeWidth={3} />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
};

export default NodeEditor;
