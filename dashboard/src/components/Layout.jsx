
import { useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

function Layout({ children }) {
  const location = useLocation()
  const editorialPages = ['/', '/world-news', '/reports']
  const themeClass = editorialPages.includes(location.pathname)
    ? 'theme-editorial'
    : 'theme-intelligence'

  return (
    <div className={`app-shell ${themeClass}`}>
      <Sidebar />

      <main className="main-content">
        <Topbar />

        {children}
      </main>
    </div>
  )
}

export default Layout
