import { useEffect, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const parsed = new Date(`${value}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function Events() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [watchlist, setWatchlist] = useState([])
  const [watchlistError, setWatchlistError] = useState('')
  const [watchlistBusy, setWatchlistBusy] = useState(false)

  useEffect(() => {
    let active = true

    async function loadEvents() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${API_BASE}/api/events?days=${days}&min_articles=2`)
        if (!response.ok) throw new Error('Unable to retrieve event clusters.')
        const result = await response.json()
        if (!active) return
        setData(result)
        setSelectedId(result.clusters?.[0]?.cluster_id ?? null)
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoading(false)
      }
    }

    loadEvents()
    return () => { active = false }
  }, [days])

  useEffect(() => {
    let active = true
    async function loadWatchlist() {
      try {
        const response = await fetch(`${API_BASE}/api/events/watchlist`)
        if (!response.ok) throw new Error('Unable to load tracked events.')
        const result = await response.json()
        if (active) setWatchlist(result.events || [])
      } catch (loadError) {
        if (active) setWatchlistError(loadError.message)
      }
    }
    loadWatchlist()
    return () => { active = false }
  }, [])

  async function toggleTrackedEvent() {
    if (!selectedCluster || watchlistBusy) return
    setWatchlistBusy(true)
    setWatchlistError('')
    const isTracked = watchlist.some((item) => item.cluster_id === selectedCluster.cluster_id)
    try {
      const response = await fetch(
        `${API_BASE}/api/events/watchlist?cluster_id=${selectedCluster.cluster_id}`,
        { method: isTracked ? 'DELETE' : 'POST' }
      )
      if (!response.ok) {
        const result = await response.json()
        throw new Error(result.detail || 'Unable to update event watchlist.')
      }
      const result = await fetch(`${API_BASE}/api/events/watchlist`)
      if (!result.ok) throw new Error('Event updated, but watchlist could not refresh.')
      const refreshed = await result.json()
      setWatchlist(refreshed.events || [])
    } catch (loadError) {
      setWatchlistError(loadError.message)
    } finally {
      setWatchlistBusy(false)
    }
  }

  const selectedCluster = data?.clusters?.find(
    (cluster) => cluster.cluster_id === selectedId
  )

  return (
    <section className="page-section regional-page events-page">
      <span className="section-kicker">GEOGRAPHIC INTELLIGENCE / EVENT DETECTION</span>
      <h1>Event Clustering</h1>
      <p>
        Identify developing stories by grouping reports that appear to describe
        the same event across different headlines and news sources.
      </p>

      <div className="trend-controls">
        <div>
          <span className="section-kicker">ANALYSIS WINDOW</span>
          <strong>Latest available {days} days of published coverage</strong>
        </div>
        <div className="trend-window-buttons" aria-label="Choose event analysis window">
          {[7, 14, 30, 90].map((value) => (
            <button
              type="button"
              key={value}
              className={days === value ? 'active' : ''}
              onClick={() => setDays(value)}
            >
              {value}D
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="regional-status">Comparing headlines, countries, topics and publication dates...</div>
      )}

      {!loading && error && (
        <div className="regional-status regional-error">
          {error} Make sure the FastAPI backend is running.
        </div>
      )}

      {!loading && data && !data.available && (
        <div className="regional-status">{data.message}</div>
      )}

      <section className="regional-panel event-watchlist">
        <div className="regional-panel-heading">
          <div>
            <span className="section-kicker">ANALYST WORKSPACE</span>
            <h3>Tracked events</h3>
          </div>
          <span>{watchlist.length} saved</span>
        </div>
        {watchlistError && <p className="regional-status regional-error">{watchlistError}</p>}
        {watchlist.length ? (
          <div className="event-watchlist-list">
            {watchlist.map((item) => (
              <div className="event-watchlist-item" key={item.cluster_id}>
                <div>
                  <strong>{item.headline}</strong>
                  <span>
                    {item.currently_detected
                      ? `${item.article_count} reports · latest ${formatDate(item.latest_seen)}`
                      : 'Not present in the latest 90-day detection window'}
                  </span>
                </div>
                <span className={item.currently_detected ? 'event-watch-status active' : 'event-watch-status'}>
                  {item.currently_detected ? 'IN CURRENT DATA' : 'NOT RECENTLY DETECTED'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="regional-empty">No tracked events yet. Select an event below and add it to your watchlist.</p>
        )}
      </section>

      {!loading && data?.available && (
        <>
          <div className="trend-period-note">
            <span>DATA THROUGH <strong>{formatDate(data.latest_data_date)}</strong></span>
            <span>WINDOW STARTS {formatDate(data.window_start)}</span>
          </div>

          <div className="regional-overview event-overview">
            <div className="regional-stat">
              <span>EVENT CLUSTERS</span>
              <strong>{data.cluster_count}</strong>
              <small>Groups containing at least two reports</small>
            </div>
            <div className="regional-stat">
              <span>ARTICLES CLUSTERED</span>
              <strong>{data.clustered_article_count}</strong>
              <small>Reports assigned to an event group</small>
            </div>
            <div className="regional-stat">
              <span>ARTICLES ANALYSED</span>
              <strong>{data.articles_analysed}</strong>
              <small>Articles with usable publication dates</small>
            </div>
            <div className="regional-stat">
              <span>UNCLUSTERED ARTICLES</span>
              <strong>{data.unclustered_article_count}</strong>
              <small>No sufficiently strong match found</small>
            </div>
          </div>

          <div className="event-workspace">
            <section className="regional-panel event-directory">
              <div className="regional-panel-heading">
                <h3>Detected event groups</h3>
                <span>{data.clusters.length} clusters</span>
              </div>

              {data.clusters.map((cluster, index) => (
                <button
                  type="button"
                  key={cluster.cluster_id}
                  className={`event-cluster-card ${selectedId === cluster.cluster_id ? 'selected' : ''}`}
                  onClick={() => setSelectedId(cluster.cluster_id)}
                >
                  <span className="event-cluster-index">EVENT {String(index + 1).padStart(2, '0')}</span>
                  <strong>{cluster.headline}</strong>
                  <span className="event-cluster-meta">
                    {cluster.article_count} reports · {cluster.sources.length} sources
                  </span>
                  <span className="event-cluster-meta">
                    {formatDate(cluster.first_seen)} — {formatDate(cluster.latest_seen)}
                  </span>
                  <span className="event-cluster-tags">
                    {cluster.countries.slice(0, 3).map((country) => country.name).join(' · ')}
                  </span>
                </button>
              ))}

              {!data.clusters.length && (
                <p className="regional-empty">
                  No multi-article event groups met the current matching threshold.
                  Try a wider analysis window.
                </p>
              )}
            </section>

            <section className="regional-panel event-profile">
              {selectedCluster ? (
                <>
                  <span className="section-kicker">EVENT INTELLIGENCE PROFILE</span>
                  <h2>{selectedCluster.headline}</h2>
                  <button
                    type="button"
                    className="event-track-button"
                    onClick={toggleTrackedEvent}
                    disabled={watchlistBusy}
                  >
                    {watchlistBusy ? 'UPDATING WATCHLIST…' : watchlist.some((item) => item.cluster_id === selectedCluster.cluster_id) ? 'REMOVE FROM WATCHLIST' : '＋ TRACK THIS EVENT'}
                  </button>
                  <p className="event-profile-summary">
                    This group contains {selectedCluster.article_count} reports
                    published between {formatDate(selectedCluster.first_seen)} and
                    {' '}{formatDate(selectedCluster.latest_seen)}.
                  </p>

                  <div className="regional-detail-stats event-detail-stats">
                    <div><span>REPORTS</span><strong>{selectedCluster.article_count}</strong></div>
                    <div><span>COUNTRIES</span><strong>{selectedCluster.countries.length}</strong></div>
                    <div><span>TOPICS</span><strong>{selectedCluster.topics.length}</strong></div>
                    <div><span>SOURCES</span><strong>{selectedCluster.sources.length}</strong></div>
                  </div>

                  <h3 className="relationship-subheading">Countries mentioned</h3>
                  <div className="event-chip-list">
                    {selectedCluster.countries.map((item) => (
                      <span key={item.name}>{item.name} <strong>{item.article_count}</strong></span>
                    ))}
                    {!selectedCluster.countries.length && <span>No country data</span>}
                  </div>

                  <h3 className="relationship-subheading">Topics represented</h3>
                  <div className="event-chip-list event-topic-chips">
                    {selectedCluster.topics.map((item) => (
                      <span key={item.name}>{item.name} <strong>{item.article_count}</strong></span>
                    ))}
                    {!selectedCluster.topics.length && <span>No topic data</span>}
                  </div>

                  <h3 className="relationship-subheading">Reporting sources</h3>
                  <div className="regional-source-list">
                    {selectedCluster.sources.map((item) => (
                      <div className="regional-source-item" key={item.name}>
                        <span>{item.name}</span>
                        <strong>{item.article_count} reports</strong>
                      </div>
                    ))}
                  </div>

                  <h3 className="relationship-subheading">Reports in this event group</h3>
                  {selectedCluster.articles.map((article) => (
                    <article className="regional-article" key={article.id}>
                      <div className="regional-article-meta">
                        <span>{article.source || 'Unknown source'}</span>
                        <time>{formatDate(article.published)}</time>
                      </div>
                      <h4>{article.title}</h4>
                      <div className="regional-article-tags">
                        {article.countries?.split(',').filter(Boolean).map((country) => (
                          <span key={country}>{country.trim()}</span>
                        ))}
                        {article.topics?.split(',').filter(Boolean).map((topic) => (
                          <span className="topic" key={topic}>{topic.trim()}</span>
                        ))}
                      </div>
                      {article.link && (
                        <a href={article.link} target="_blank" rel="noreferrer">
                          Read original report ↗
                        </a>
                      )}
                    </article>
                  ))}
                </>
              ) : (
                <p className="regional-empty">
                  Select an event group to inspect its reports and coverage profile.
                </p>
              )}
            </section>
          </div>

          <p className="regional-data-note">
            METHODOLOGY — Reports are grouped when their publication dates are
            within ten days, their headlines share at least two meaningful terms,
            and they share a recognised country or topic. Groups are candidate
            event clusters, not verified facts. Similar headlines can still refer
            to separate developments; review the linked source reports before
            drawing conclusions. Articles without valid dates are excluded.
          </p>
        </>
      )}
    </section>
  )
}

export default Events
