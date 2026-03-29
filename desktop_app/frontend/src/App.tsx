import { useAppStore } from './store';
import ProjectManager from './components/ProjectManager';
import MassiveConfigEditor from './components/MassiveConfigEditor';
import NodeEditor from './components/NodeEditor';

export default function App() {
  const { view } = useAppStore();

  return (
    <div className="app-layout h-screen w-screen overflow-hidden bg-dark">
      {view === 'project-manager' && <ProjectManager />}
      {view === 'config-editor' && <MassiveConfigEditor />}
      {view === 'node-studio' && <NodeEditor isVisible={true} onClose={() => {}} />}
    </div>
  );
}
