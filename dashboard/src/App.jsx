
import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'

import Home from './pages/Home'
import WorldNews from './pages/WorldNews'
import Countries from './pages/Countries'
import Intelligence from './pages/Intelligence'
import Research from './pages/Research'
import Reports from './pages/Reports'
import Trends from './pages/Trends'
import Events from './pages/Events'
import SourceAnalysis from './pages/SourceAnalysis'
import StrategicSignals from './pages/StrategicSignals'

import './App.css'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/world-news" element={<WorldNews />} />
        <Route path="/countries" element={<Countries />} />
        <Route path="/intelligence" element={<Intelligence />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/events" element={<Events />} />
        <Route path="/sources" element={<SourceAnalysis />} />
        <Route path="/signals" element={<StrategicSignals />} />
        <Route path="/research" element={<Research />} />
        <Route path="/reports" element={<Reports />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
