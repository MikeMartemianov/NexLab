import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import HUDWidget from './components/HUDWidget.tsx'

const isHUD = window.location.hash.includes('/hud');

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {isHUD ? <HUDWidget /> : <App />}
  </StrictMode>,
)
