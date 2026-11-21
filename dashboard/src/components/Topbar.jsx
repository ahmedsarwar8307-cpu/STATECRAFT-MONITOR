
import { Search, Clock3 } from 'lucide-react'
import { useLocation } from 'react-router-dom'

const pageNames = {
  '/': 'OVERVIEW',
  '/world-news': 'WORLD NEWS',
  '/countries': 'REGIONS & COUNTRIES',
  '/intelligence': 'INTELLIGENCE',
  '/trends': 'GEOPOLITICAL TRENDS',
  '/research': 'RESEARCH',
  '/reports': 'REPORTS & BRIEFINGS',
}

function Topbar() {
  const location = useLocation()
  const currentPage = pageNames[location.pathname] || 'OVERVIEW'

  return (
    <header className="topbar">
      <div className="breadcrumb">
        GLOBAL INTELLIGENCE <span>/</span> {currentPage}
      </div>

      <div className="topbar-right">
        <button className="icon-button" aria-label="Search">
          <Search size={18} />
        </button>

        <button className="icon-button" aria-label="Activity">
          <Clock3 size={18} />
        </button>

        <div className="topbar-divider"></div>
        <span className="edition">GLOBAL EDITION</span>
      </div>
    </header>
  )
}

export default Topbar
