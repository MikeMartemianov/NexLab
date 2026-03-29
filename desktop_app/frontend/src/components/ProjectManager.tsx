import { useState, useEffect } from 'react';
import { useAppStore } from '../store';
import { Folder, Plus, ArrowRight, Shield, Zap, Activity } from 'lucide-react';

const ProjectManager = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const { setProject, setConfig, setView } = useAppStore();

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/projects')
      .then(res => res.json())
      .then(data => setProjects(data.projects));
  }, []);

  const openProject = async (path: string) => {
    const res = await fetch('http://127.0.0.1:8000/api/project/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    const data = await res.json();
    setProject({ name: path.split(/[/\\]/).pop() || '', path, has_config: true });
    setConfig(data.config);
    setView('config-editor');
  };

  return (
    <div className="project-manager h-screen w-screen flex flex-col items-center justify-center p-12 overflow-hidden" 
      style={{ background: 'radial-gradient(circle at 50% 10%, rgba(99, 102, 241, 0.15), transparent), var(--bg-dark)' }}>
      
      <div className="text-center mb-12 animate-in fade-in slide-in-from-top duration-700">
        <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
          NexLab Professional
        </h1>
        <p className="text-gray-400 text-lg">Agentic Framework & Visual Orchestrator v1.4.0</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-6xl">
        <div className="glass-card flex flex-col" style={{ minHeight: '400px' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold flex items-center gap-3">
              <Folder className="text-accent-base" /> Open Project
            </h2>
            <span className="text-xs text-dim uppercase tracking-widest">Local Workspace</span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {projects.map((p, i) => (
              <div key={i} className="group p-4 mb-3 rounded-xl border border-muted bg-base/50 hover:border-accent-base hover:bg-elevated transition-all cursor-pointer flex items-center justify-between"
                onClick={() => openProject(p.path)}>
                <div>
                  <div className="font-semibold text-main group-hover:text-accent-base transition-colors">{p.name}</div>
                  <div className="text-xs text-dim truncate max-w-[300px]">{p.path}</div>
                </div>
                <ArrowRight size={18} className="text-dim group-hover:text-accent-base group-hover:translate-x-1 transition-all" />
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card flex flex-col bg-accent-glow/5 border-accent-base/20">
          <h2 className="text-xl font-bold flex items-center gap-3 mb-6">
            <Plus className="text-accent-base" /> New Intelligence
          </h2>
          
          <div className="space-y-6">
            <div className="p-4 rounded-xl border border-muted bg-base/30">
              <div className="flex items-center gap-3 mb-2">
                <Shield className="text-success" size={20} />
                <span className="font-bold">Autonomous Swarm</span>
              </div>
              <p className="text-xs text-muted">Multi-agent orchestrator with Docker isolation and self-healing logic.</p>
            </div>
            
            <div className="p-4 rounded-xl border border-muted bg-base/30">
              <div className="flex items-center gap-3 mb-2">
                <Zap className="text-warning" size={20} />
                <span className="font-bold">Fast-Stream Assistant</span>
              </div>
              <p className="text-xs text-muted">Optimized for low-latency coding tasks and real-time project analysis.</p>
            </div>

            <div className="p-4 rounded-xl border border-muted bg-base/30">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="text-accent-base" size={20} />
                <span className="font-bold">Deep Reasoning Lab</span>
              </div>
              <p className="text-xs text-muted">High-fidelity thinking iterations for mathematically complex problems.</p>
            </div>

            <button className="btn btn-primary w-full py-4 text-lg mt-4 shadow-xl shadow-accent-glow">
              Scaffold New Project
            </button>
          </div>
        </div>
      </div>

      <div className="mt-12 text-dim text-xs tracking-tighter opacity-50">
        NEXLAB KERNEL v1.4.0-STABLE // SYSTEM READY
      </div>
    </div>
  );
};

export default ProjectManager;
