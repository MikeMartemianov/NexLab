import { useState, useEffect } from 'react';
import { useAppStore } from '../store';
import { Settings, Save, ArrowRight, Shield, Zap, Database, Activity, Cpu } from 'lucide-react';

const MassiveConfigEditor = () => {
  const { config, setConfig, setView } = useAppStore();
  const [localConfig, setLocalConfig] = useState<any>(config || {});
  const [activeTab, setActiveTab] = useState('core');
  const [schema, setSchema] = useState<any>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/config/schema')
      .then(res => res.json())
      .then(data => setSchema(data));
  }, []);

  const update = (key: string, value: any) => {
    setLocalConfig((prev: any) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    await fetch('http://127.0.0.1:8000/api/config/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: localConfig })
    });
    setConfig(localConfig);
  };

  const getIcon = (id: string) => {
    switch (id) {
      case 'core': return <Settings size={18} />;
      case 'model': return <Cpu size={18} />;
      case 'components': return <Zap size={18} />;
      case 'memory': return <Database size={18} />;
      default: return <Activity size={18} />;
    }
  };

  if (!schema) return <div className="p-12 text-dim">Synthesizing Parameter Schema...</div>;

  return (
    <div className="h-screen w-screen flex bg-dark overflow-hidden">
      {/* Sidebar Tabs */}
      <div className="w-64 border-r border-muted bg-surface flex flex-col p-6 gap-2">
        <div className="text-xs text-dim uppercase tracking-widest mb-4">Configuration</div>
        {schema.groups.map((g: any) => (
          <div key={g.id} 
            className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${activeTab === g.id ? 'bg-accent-glow text-accent-base border border-accent-base/30' : 'text-muted hover:bg-elevated'}`}
            onClick={() => setActiveTab(g.id)}>
            {getIcon(g.id)}
            <span className="font-medium text-sm">{g.label}</span>
          </div>
        ))}

        <div className="mt-auto space-y-3">
          <button className="btn btn-secondary w-full flex items-center justify-center gap-2 py-3" onClick={handleSave}>
            <Save size={16} /> Save Changes
          </button>
          <button className="btn btn-primary w-full flex items-center justify-center gap-2 py-4 shadow-lg shadow-accent-glow"
            onClick={() => setView('node-studio')}>
            Open Node Studio <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col p-12 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl w-full mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold flex items-center gap-4">
              {schema.groups.find((g: any) => g.id === activeTab)?.label}
            </h1>
            <p className="text-muted mt-2">Fine-tune the agent's core performance and logic parameters.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {schema.groups.find((g: any) => g.id === activeTab)?.params.map((p: any) => (
              <div key={p.id} className="form-group flex flex-col gap-2 p-4 rounded-2xl bg-surface/30 border border-muted hover:border-accent-base/20 transition-all">
                <label className="text-sm font-semibold text-main flex justify-between">
                  {p.label}
                  {p.type === 'range' && <span className="text-accent-base font-mono">{localConfig[p.id] ?? p.default}</span>}
                </label>
                
                {p.type === 'string' && (
                  <input className="bg-base border-muted p-3 rounded-xl text-sm outline-none focus:border-accent-base" 
                    value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)} />
                )}

                {p.type === 'password' && (
                  <input type="password" className="bg-base border-muted p-3 rounded-xl text-sm outline-none focus:border-accent-base" 
                    value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)} />
                )}

                {p.type === 'number' && (
                  <input type="number" className="bg-base border-muted p-3 rounded-xl text-sm outline-none focus:border-accent-base" 
                    value={localConfig[p.id] ?? 0} onChange={e => update(p.id, parseInt(e.target.value))} />
                )}

                {p.type === 'boolean' && (
                  <div className={`p-1 rounded-full w-14 h-8 transition-all cursor-pointer relative ${localConfig[p.id] ? 'bg-accent-base' : 'bg-muted'}`}
                    onClick={() => update(p.id, !localConfig[p.id])}>
                    <div className={`w-6 h-6 bg-white rounded-full absolute top-1 transition-all ${localConfig[p.id] ? 'left-7' : 'left-1'}`} />
                  </div>
                )}

                {p.type === 'range' && (
                  <input type="range" min={p.min} max={p.max} step={p.step} className="accent-accent-base"
                    value={localConfig[p.id] ?? 0.7} onChange={e => update(p.id, parseFloat(e.target.value))} />
                )}

                {p.type === 'select' && (
                  <select className="bg-base border-muted p-3 rounded-xl text-sm outline-none focus:border-accent-base"
                    value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)}>
                    {p.options.map((o: string) => <option key={o} value={o}>{o}</option>)}
                  </select>
                )}
              </div>
            ))}
          </div>

          <div className="mt-12 glass-card border-warning/20 bg-warning/5">
             <div className="flex gap-4 items-center">
                <Shield className="text-warning" />
                <div className="text-xs text-muted leading-relaxed">
                  <strong>SYSTEM NOTICE:</strong> Changing these parameters will update <code>config.yaml</code> in real-time. 
                  Some changes may require restarting the agent to take full effect in the runtime environment.
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MassiveConfigEditor;
