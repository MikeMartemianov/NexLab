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

  if (!schema) return (
    <div className="flex h-screen w-screen items-center justify-center bg-dark text-accent-base">
      <Zap className="animate-pulse mr-3" />
      <span className="font-bold tracking-widest">CALIBRATING NEURAL SCHEMA...</span>
    </div>
  );

  const activeGroup = schema.groups.find((g: any) => g.id === activeTab);

  return (
    <div className="h-screen w-screen flex bg-dark overflow-hidden transition-colors duration-500">
      {/* Sidebar Navigation */}
      <div className="w-72 border-r border-muted bg-surface flex flex-col p-6 gap-2 z-20 shadow-xl">
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-10 h-10 rounded-xl bg-accent-base flex items-center justify-center text-white shadow-lg shadow-accent-glow">
            <Cpu size={22} />
          </div>
          <div>
            <div className="font-bold text-main leading-tight">NexLab v2.0</div>
            <div className="text-[10px] text-accent-base font-bold tracking-widest uppercase">Radiant Pro</div>
          </div>
        </div>

        <div className="text-[10px] text-dim font-bold uppercase tracking-widest mb-2 px-2">Control Modules</div>
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">
          {schema.groups.map((g: any) => (
            <div key={g.id} 
              className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all mb-1 ${activeTab === g.id ? 'bg-accent-glow text-accent-base border border-accent-base/30' : 'text-muted hover:bg-elevated'}`}
              onClick={() => setActiveTab(g.id)}>
              {getIcon(g.id)}
              <span className="font-semibold text-sm">{g.label}</span>
            </div>
          ))}
        </div>

        <div className="pt-6 border-t border-muted space-y-3">
          <button className="btn btn-secondary w-full py-3 flex items-center justify-center gap-2" onClick={handleSave}>
            <Save size={16} /> Save Configuration
          </button>
          <button className="btn btn-primary w-full py-4 flex items-center justify-center gap-2 shadow-xl shadow-accent-glow"
            onClick={() => setView('node-studio')}>
            Launch Orchestrator <ArrowRight size={18} />
          </button>
        </div>
      </div>

      {/* Main Parameters Panel */}
      <div className="flex-1 flex flex-col bg-dark overflow-hidden relative">
        {/* Background Accent */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-glow blur-[120px] rounded-full opacity-20 -mr-48 -mt-48 pointer-events-none" />

        <div className="flex-1 overflow-y-auto p-12 custom-scrollbar z-10">
          <div className="max-w-5xl mx-auto">
            <header className="mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-glow border border-accent-base/20 text-accent-base text-[10px] font-bold tracking-widest uppercase mb-4">
                Module: {activeTab}
              </div>
              <h1 className="text-4xl font-extrabold text-main mb-3">
                {activeGroup?.label}
              </h1>
              <p className="text-muted text-lg max-w-2xl leading-relaxed">
                Configure advanced {activeGroup?.label.toLowerCase()} behaviors. These parameters directly influence the swarm's decision-making and execution logic.
              </p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {activeGroup?.params.map((p: any) => (
                <div key={p.id} className="group flex flex-col gap-3 p-5 rounded-2xl bg-surface/40 border border-muted hover:border-accent-base/30 hover:bg-surface/60 transition-all duration-300">
                  <div className="flex justify-between items-center">
                    <label className="text-xs font-bold text-main uppercase tracking-wider">
                      {p.label}
                    </label>
                    {p.type === 'range' && (
                      <span className="px-2 py-0.5 rounded-md bg-accent-glow text-accent-base font-mono text-xs font-bold">
                        {localConfig[p.id] ?? 0.7}
                      </span>
                    )}
                  </div>
                  
                  {p.type === 'string' && (
                    <input className="bg-base border border-muted p-3 rounded-xl text-sm text-main outline-none focus:border-accent-base focus:ring-4 focus:ring-accent-glow/10 transition-all" 
                      placeholder={`Enter ${p.label}...`}
                      value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)} />
                  )}

                  {p.type === 'password' && (
                    <input type="password" className="bg-base border border-muted p-3 rounded-xl text-sm text-main outline-none focus:border-accent-base focus:ring-4 focus:ring-accent-glow/10 transition-all" 
                      placeholder="••••••••••••••••"
                      value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)} />
                  )}

                  {p.type === 'number' && (
                    <input type="number" className="bg-base border border-muted p-3 rounded-xl text-sm text-main outline-none focus:border-accent-base focus:ring-4 focus:ring-accent-glow/10 transition-all" 
                      value={localConfig[p.id] ?? 0} onChange={e => update(p.id, parseInt(e.target.value))} />
                  )}

                  {p.type === 'boolean' && (
                    <div className="flex items-center gap-3">
                      <div className={`p-1 rounded-full w-12 h-6 transition-all cursor-pointer relative ${localConfig[p.id] ? 'bg-accent-base' : 'bg-muted/50'}`}
                        onClick={() => update(p.id, !localConfig[p.id])}>
                        <div className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-all ${localConfig[p.id] ? 'left-7' : 'left-1'}`} />
                      </div>
                      <span className="text-xs font-semibold text-muted">{localConfig[p.id] ? 'Enabled' : 'Disabled'}</span>
                    </div>
                  )}

                  {p.type === 'range' && (
                    <input type="range" min={p.min} max={p.max} step={p.step} className="accent-accent-base h-2 w-full"
                      value={localConfig[p.id] ?? 0.7} onChange={e => update(p.id, parseFloat(e.target.value))} />
                  )}

                  {p.type === 'select' && (
                    <select className="bg-base border border-muted p-3 rounded-xl text-sm text-main outline-none focus:border-accent-base transition-all"
                      value={localConfig[p.id] ?? ''} onChange={e => update(p.id, e.target.value)}>
                      {p.options?.map((o: string) => <option key={o} value={o}>{o}</option>)}
                    </select>
                  )}
                </div>
              ))}
            </div>

            <footer className="mt-16 p-8 rounded-3xl bg-accent-glow/5 border border-accent-base/10 flex items-start gap-6">
              <div className="w-12 h-12 rounded-2xl bg-accent-base flex items-center justify-center text-white shrink-0">
                <Shield size={24} />
              </div>
              <div>
                <h4 className="text-main font-bold mb-1">Configuration Integrity Engine</h4>
                <p className="text-muted text-sm leading-relaxed max-w-2xl">
                  Nexus v2.0 automatically validates changes in real-time. Modifications to <code>config.yaml</code> are atomic and secure. 
                  Parameters requiring a reboot will be highlighted with a red pulse in the status bar.
                </p>
              </div>
            </footer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MassiveConfigEditor;
