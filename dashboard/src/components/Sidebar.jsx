
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Newspaper,
  Globe2,
  Crosshair,
  TrendingUp,
  Activity,
  Radar,
  Network,
  Search,
  FileText,
} from 'lucide-react'

const navigation = [
  { name: 'Overview', path: '/', icon: LayoutDashboard },
  { name: 'World News', path: '/world-news', icon: Newspaper },
  { name: 'Regions & Countries', path: '/countries', icon: Globe2 },
  { name: 'Intelligence', path: '/intelligence', icon: Crosshair },
  { name: 'Geopolitical Trends', path: '/trends', icon: TrendingUp },
  { name: 'Event Clustering', path: '/events', icon: Network },
  { name: 'Strategic Signals', path: '/signals', icon: Radar },
  { name: 'Source Reliability', path: '/sources', icon: Activity },
  { name: 'Research', path: '/research', icon: Search },
  { name: 'Reports & Briefings', path: '/reports', icon: FileText },
]

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">S</div>
        <div>
          <h2>Statecraft</h2>
          <span>MONITOR</span>
        </div>
      </div>

      <div className="nav-label">WORKSPACE</div>

      <nav className="navigation">
        {navigation.map((item) => {
          const Icon = item.icon

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={18} strokeWidth={1.7} />
              <span>{item.name}</span>
            </NavLink>
          )
        })}
      </nav>

      <div className="sidebar-bottom">
        <div className="system-status">
          <span className="status-dot"></span>
          SYSTEM OPERATIONAL
        </div>

        <div className="profile">
          <div className="profile-avatar">A</div>
          <div>
            <strong>Analyst Workspace</strong>
            <span>Independent Research</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
