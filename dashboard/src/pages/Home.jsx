
function Home() {
  return (
    <>
      <section className="welcome-section">
        <div>
          <div className="eyebrow">
            <span className="status-dot"></span>
            GLOBAL SITUATION OVERVIEW
          </div>

          <h1>
            The world, <em>under observation.</em>
          </h1>

          <p>
            Understand the developments, decisions and forces
            shaping the international order.
          </p>
        </div>

        <div className="date-panel">
          <span>INTELLIGENCE DESK</span>
          <strong>GLOBAL MONITOR</strong>
          <small>INDEPENDENT RESEARCH PLATFORM</small>
        </div>
      </section>

      <section className="featured-section">
        <div className="section-heading">
          <div>
            <span className="section-kicker">EDITOR'S SELECTION</span>
            <h2>Developments to watch</h2>
          </div>
          <span className="section-meta">01 / FEATURED</span>
        </div>

        <div className="featured-card">
          <div className="featured-image">
            <div className="image-overlay">
              <span>GLOBAL AFFAIRS</span>
              <span>FEATURED ANALYSIS</span>
            </div>
          </div>

          <div className="featured-copy">
            <span className="story-category">STRATEGIC OUTLOOK</span>

            <h2>
              Understanding a world shaped by shifting
              geopolitical realities.
            </h2>

            <p>
              Explore the decisions, relationships and emerging
              developments influencing global affairs.
            </p>

            <button className="read-button">
              EXPLORE ANALYSIS <span>↗</span>
            </button>
          </div>
        </div>
      </section>

      <section className="lower-grid">
        <div className="developments-panel">
          <div className="section-heading">
            <div>
              <span className="section-kicker">GLOBAL COVERAGE</span>
              <h2>Latest developments</h2>
            </div>
            <span className="view-all">VIEW ALL ↗</span>
          </div>

          <div className="empty-state">
            <div className="empty-icon">◈</div>
            <h3>Intelligence feed awaiting connection</h3>
            <p>
              Your collected news and developments will appear
              here when we connect the database.
            </p>
          </div>
        </div>

        <aside className="intelligence-panel">
          <span className="section-kicker">RESEARCH ENVIRONMENT</span>
          <h2>Intelligence tools</h2>

          <div className="tool-item">
            <span>◎</span>
            <div>
              <strong>Situation Map</strong>
              <small>Explore global developments</small>
            </div>
            <span>↗</span>
          </div>

          <div className="tool-item">
            <span>⌘</span>
            <div>
              <strong>Country Relations</strong>
              <small>Explore geopolitical connections</small>
            </div>
            <span>↗</span>
          </div>

          <div className="tool-item">
            <span>▤</span>
            <div>
              <strong>Research Analyst</strong>
              <small>Investigate with source-backed context</small>
            </div>
            <span>↗</span>
          </div>

          <div className="panel-footer">
            STATECRAFT MONITOR <span>·</span> RESEARCH
          </div>
        </aside>
      </section>

      <footer className="footer">
        <span>STATECRAFT MONITOR</span>
        <span>GLOBAL AFFAIRS · INTELLIGENCE · RESEARCH</span>
      </footer>
    </>
  )
}

export default Home
