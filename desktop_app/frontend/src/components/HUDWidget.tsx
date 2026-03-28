import { useEffect, useState } from 'react';
import { Activity, Brain, Cpu, MemoryStick } from 'lucide-react';

const HUDWidget = () => {
  const [metrics, setMetrics] = useState({
    cpu: 0,
    vram: 0,
    thought: "Idling...",
    agent: "NexLab Core"
  });

  useEffect(() => {
    // Simulated connection to NexLab backend metrics
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        cpu: Math.floor(Math.random() * 20),
        vram: Math.floor(1000 + Math.random() * 500),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(15, 23, 42, 0.4)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderRadius: '16px',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      color: '#e2e8f0',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      overflow: 'hidden',
      boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
      userSelect: 'none'
    }}>
      {/* Drag handle */}
      <div 
        className="pywebview-drag-region"
        style={{
          height: '24px',
          background: 'rgba(255,255,255,0.05)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          cursor: 'move'
        }}
      >
        <div style={{ width: '40px', height: '4px', background: 'rgba(255,255,255,0.2)', borderRadius: '2px' }} />
      </div>

      <div style={{ padding: '16px', flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8' }}>
          <Brain size={18} />
          <span style={{ fontWeight: 600, fontSize: '14px' }}>{metrics.agent}</span>
        </div>

        <div style={{ fontSize: '12px', color: '#94a3b8', background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '6px' }}>
          {metrics.thought}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', fontSize: '11px', color: '#64748b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Cpu size={12} /> {metrics.cpu}%
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <MemoryStick size={12} /> {metrics.vram} MB
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#22c55e' }}>
            <Activity size={12} /> Active
          </div>
        </div>
      </div>
    </div>
  );
};

export default HUDWidget;
