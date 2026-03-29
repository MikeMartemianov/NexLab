import { useAppStore } from './store';
import ProjectManager from './components/ProjectManager';
import MassiveConfigEditor from './components/MassiveConfigEditor';
import NodeEditor from './components/NodeEditor';
import { Sun, Moon, Cpu } from 'lucide-react';

export default function App() {
  const { view, theme, setTheme } = useAppStore();

  return (
    <div className={`app-layout h-screen w-screen overflow-hidden ${theme === 'light' ? 'light-theme' : ''}`}>
      {/* Universal Activity Bar with Theme Toggle */}
      <div className="activity-bar">
        <div className="action-btn active">
          <Cpu size={20} />
        </div>
        <div className="spacer" />
        <div className="action-btn theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </div>
      </div>

      <div className="main-area">
        {view === 'project-manager' && <ProjectManager />}
        {view === 'config-editor' && <MassiveConfigEditor />}
        {view === 'node-studio' && <NodeEditor isVisible={true} onClose={() => {}} />}
      </div>
    </div>
  );
}
