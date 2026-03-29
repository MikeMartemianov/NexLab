import { useState, useEffect } from 'react';
import { useAppStore } from '../store';
import { Folder, Plus, ArrowRight, Shield, Zap, Activity, Cpu } from 'lucide-react';

const ProjectManager = () => {
  const [projects, setProjects] = useState<any[]>([]);
  const { setProject, setConfig, setView } = useAppStore();
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    refreshProjects();
  }, []);

  const refreshProjects = () => {
    fetch('http://127.0.0.1:8000/api/projects')
      .then(res => res.json())
      .then(data => setProjects(data.projects || []))
      .catch(err => console.error("Failed to fetch projects:", err));
  };

  const openProject = async (path: string) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/project/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
      });
      const data = await res.json();
      setProject({ name: path.split(/[/\\]/).pop() || '', path, has_config: true });
      setConfig(data.config);
      setView('config-editor');
    } catch (err) {
      console.error("Failed to open project:", err);
    }
  };

  const createProject = async () => {
    if (!newProjectName.trim()) return;
    setIsCreating(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/project/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProjectName })
      });
      const data = await res.json();
      if (res.ok) {
        await openProject(data.path);
      } else {
        alert(data.detail || "Error creating project");
      }
    } catch (err) {
      console.error("Failed to create project:", err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="project-manager h-screen w-screen flex flex-col items-center justify-center p-12 overflow-hidden" 
      style={{ background: 'radial-gradient(circle at 50% 10%, rgba(99, 102, 241, 0.15), transparent), var(--bg-dark)' }}>
      
      <div className="text-center mb-12 animate-in fade-in slide-in-from-top duration-700">
        <div className="inline-flex items-center justify-center p-3 bg-accent-glow rounded-2xl mb-4 border border-accent-base/20">
          <Cpu className="text-accent-base" size={40} />
        </div>
        <h1 className="text-5xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-text-main to-text-muted">
          NexLab Radiant Pro+
        </h1>
        <p className="text-muted text-lg font-medium opacity-80 tracking-wide uppercase text-[12px]">Agentic Orchestration Framework v2.1.0</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-6xl z-10">
        {/* Open Project Section */}
        <div className="glass-card flex flex-col p-8 transition-all hover:border-accent-base/30" style={{ minHeight: '450px' }}>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-bold flex items-center gap-3 text-main">
              <Folder className="text-accent-base" /> Active Workspaces
            </h2>
            <span className="text-[10px] text-accent-base font-bold uppercase tracking-widest bg-accent-glow px-2 py-1 rounded">Local</span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {projects.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-dim opacity-50 space-y-2">
                <Activity size={48} className="animate-pulse" />
                <p className="text-sm font-medium">No projects detected in root</p>
              </div>
            ) : projects.map((p, i) => (
              <div key={i} className="group p-5 mb-4 rounded-2xl border border-muted bg-base/50 hover:border-accent-base hover:bg-elevated transition-all cursor-pointer flex items-center justify-between"
                onClick={() => openProject(p.path)}>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-main group-hover:text-accent-base transition-colors truncate">{p.name}</div>
                  <div className="text-[10px] text-muted truncate opacity-60 mt-1 font-mono">{p.path}</div>
                </div>
                <div className="ml-4 w-8 h-8 rounded-full bg-accent-glow flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                  <ArrowRight size={16} className="text-accent-base group-hover:translate-x-0.5" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* New Project Section */}
        <div className="glass-card flex flex-col p-8 bg-accent-glow/5 border-accent-base/20 transition-all hover:bg-accent-glow/10">
          <h2 className="text-xl font-bold flex items-center gap-3 mb-8 text-main">
            <Plus className="text-accent-base" /> New Intelligence
          </h2>
          
          <div className="space-y-6">
            <div className="space-y-4 mb-8">
               <div className="form-group">
                 <label className="text-[10px] font-bold uppercase text-dim tracking-widest mb-2 block">Project Identifier</label>
                 <input 
                   type="text" 
                   className="w-full bg-base border border-muted p-4 rounded-xl text-main outline-none focus:border-accent-base transition-all" 
                   placeholder="e.g. CoderAgent-v1" 
                   value={newProjectName}
                   onChange={e => setNewProjectName(e.target.value)}
                 />
               </div>
            </div>

            <div className="hidden lg:block space-y-4">
               <div className="p-4 rounded-2xl border border-muted bg-base/40 flex items-start gap-4 hover:border-accent-base/20 transition-all">
                 <Shield className="text-success mt-1" size={20} />
                 <div>
                   <div className="text-sm font-bold text-main">Autonomous Swarm</div>
                   <p className="text-[11px] text-muted mt-1 leading-relaxed">Isolated Docker orchestration with self-healing feedback loops.</p>
                 </div>
               </div>
               
               <div className="p-4 rounded-2xl border border-muted bg-base/40 flex items-start gap-4 hover:border-accent-base/20 transition-all">
                 <Zap className="text-warning mt-1" size={20} />
                 <div>
                   <div className="text-sm font-bold text-main">Fast-Stream Assistant</div>
                   <p className="text-[11px] text-muted mt-1 leading-relaxed">Low-latency context-aware analysis for real-time coding tasks.</p>
                 </div>
               </div>
            </div>

            <button 
              className={`btn btn-primary w-full py-5 text-lg font-bold mt-4 shadow-2xl shadow-accent-glow flex items-center justify-center gap-3 ${isCreating ? 'opacity-50 cursor-wait' : ''}`}
              onClick={createProject}
              disabled={isCreating}
            >
              {isCreating ? <Zap className="animate-spin" size={20} /> : <Plus size={20} />}
              Initialize Archetype
            </button>
          </div>
        </div>
      </div>

      <div className="absolute bottom-10 text-dim text-[10px] font-bold tracking-[0.3em] opacity-40 animate-pulse">
        NEXLAB KERNEL v2.1.0-STABLE // RADIATION PRO+ SYSTEM ACTIVE
      </div>
    </div>
  );
};

export default ProjectManager;
