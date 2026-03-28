import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Cpu, Database, Zap, HardDrive, ShieldCheck } from 'lucide-react';

export type NodeStatus = 'idle' | 'running' | 'success' | 'error';

export interface SmartNodeData {
  label: string;
  type: 'agent' | 'tool' | 'source' | 'sandbox' | 'memory';
  status?: NodeStatus;
  lastOutput?: string;
}

const SmartNode = ({ data }: NodeProps) => {
  const { label, type, status = 'idle' } = data as unknown as SmartNodeData;

  const getIcon = () => {
    switch (type) {
      case 'agent': return <BrainIcon />;
      case 'tool': return <Zap size={16} />;
      case 'source': return <Database size={16} />;
      case 'sandbox': return <ShieldCheck size={16} />;
      case 'memory': return <HardDrive size={16} />;
      default: return <Cpu size={16} />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'var(--accent-base)';
      case 'success': return 'var(--success)';
      case 'error': return 'var(--error)';
      default: return 'var(--border-active)';
    }
  };

  return (
    <div className={`smart-node ${status}`} style={{
      padding: '12px 16px',
      borderRadius: '12px',
      background: 'var(--bg-elevated)',
      border: `1px solid ${getStatusColor()}`,
      minWidth: '180px',
      boxShadow: status === 'running' ? '0 0 15px var(--accent-glow)' : '0 4px 12px rgba(0,0,0,0.2)',
      transition: 'all 0.3s ease',
      color: 'var(--text-main)',
      position: 'relative',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: 'var(--accent-base)', border: 'none' }} />
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ 
          color: getStatusColor(),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {getIcon()}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
            {type}
          </div>
          <div style={{ fontSize: '14px', fontWeight: 500 }}>{label}</div>
        </div>
      </div>

      {status === 'running' && (
        <div className="pulse-ring" />
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: 'var(--accent-base)', border: 'none' }} />
    </div>
  );
};

const BrainIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.105 4 4 0 0 0 5.327 2.7OpenRouter 4 4 0 0 0 5.12 1.435A4 4 0 0 0 21.03 14.77a4 4 0 0 0-1.526-7.77 4 4 0 0 0-2.526-5.77A3.001 3.001 0 0 0 12 5Z" />
    <path d="M9 13a4.5 4.5 0 0 0 3 4" />
    <path d="M15 13a4.5 4.5 0 0 1-3 4" />
    <path d="M12 5v4" />
  </svg>
);

export default SmartNode;
