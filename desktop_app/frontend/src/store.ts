import { create } from 'zustand';

interface Project {
  name: string;
  path: string;
  has_config: boolean;
}

interface AppState {
  currentProject: Project | null;
  config: any | null;
  view: 'project-manager' | 'config-editor' | 'node-studio';
  
  setProject: (project: Project | null) => void;
  setConfig: (config: any) => void;
  setView: (view: 'project-manager' | 'config-editor' | 'node-studio') => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentProject: null,
  config: null,
  view: 'project-manager',

  setProject: (project) => set({ currentProject: project }),
  setConfig: (config) => set({ config }),
  setView: (view) => set({ view }),
}));
