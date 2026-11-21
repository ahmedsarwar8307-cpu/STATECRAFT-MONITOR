import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function TrendList({ title, items, emptyMessage }) {
  return (
    <section className="regional-panel trend-list-panel">
      <div className="regional-panel-heading">
        <h3>{title}</h3>
        <span>Recent vs previous period</span>
      </div>

      {items.length ? items.map((item) => (
        <div className="trend-row" key={item.name}>
          <div className="trend-row-main">
            <strong>{item.name}</strong>
            <span>{item.recent_count} recent · {item.previous_count} previous</span>
          </div>
          <div className="trend-row-result">
            <strong className={`trend-change trend-${item.status}`}>
              {item.change > 0 ? '+' : ''}{item.change}
            </strong>
            <span className={`trend-status trend-${item.status}`}>
              {item.status === 'new' ? 'NEW' : item.status.toUpperCase()}
            </span>
          </div>
        </div>
      )) : (
        <p className="regional-empty">{emptyMessage}</p>
      )}
    </section>
  )
}

function Trends() {
  const [days, setDays] = useState(7)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadTrends() {
      setLoading(true)
      setError('')

      try {
        const response = await fetch(`${API_BASE}/api/trends?days=${days}`)
        if (!response.ok) throw new Error('Unable to retrieve coverage trends.')
        const result = await response.json()
        if (active) setData(result)
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoading(false)
      }
    }

    loadTrends()
    return () => { active = false }
  }, [days])

  const maxTimelineValue = useMemo(() => {
    if (!data?.timeline?.length) return 1
    return Math.max(...data.timeline.map((item) => item.article_count), 1)
  }, [data])

  const risingTopics = useMemo(
    () => data?.topics?.filter((item) => item.status === 'rising' || item.status === 'new') ?? [],
    [data]
  )
  const decliningTopics = useMemo(
    () => data?.topics?.filter((item) => item.status === 'declining') ?? [],
    [data]
  )

  return (
    <section className="page-section regional-page trends-page">
      <span className="section-kicker">GEOGRAPHIC INTELLIGENCE / TEMPORAL ANALYSIS</span>
      <h1>Geopolitical Trends</h1>
      <p>
        Track changes in country and topic coverage across the collected news
        dataset. Compare the latest reporting window with the preceding period
        to identify shifts in editorial attention.
      </p>

      <div className="trend-controls">
        <div>
          <span className="section-kicker">COMPARISON WINDOW</span>
          <strong>{days} days vs previous {days} days</strong>
        </div>
        <div className="trend-window-buttons" aria-label="Choose comparison window">
          {[7, 14, 30].map((value) => (
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
        <div className="regional-status">Calculating coverage trends from publication dates...</div>
      )}

      {!loading && error && (
        <div className="regional-status regional-error">
          {error} Make sure the FastAPI backend is running.
        </div>
      )}

      {!loading && data && !data.available && (
        <div className="regional-status">
          {data.message || 'Trend analysis is not available for the current dataset.'}
        </div>
      )}

      {!loading && data?.available && (
        <>
          <div className="trend-period-note">
            <span>DATA THROUGH <strong>{formatDate(data.latest_data_date)}</strong></span>
            <span>BASED ON {data.dated_article_count} ARTICLES WITH VALID DATES</span>
          </div>

          <div className="regional-overview trend-overview">
            <div className="regional-stat">
              <span>RECENT PERIOD</span>
              <strong>{data.recent_window.article_count}</strong>
              <small>{formatDate(data.recent_window.start)} – {formatDate(data.recent_window.end)}</small>
            </div>
            <div className="regional-stat">
              <span>PREVIOUS PERIOD</span>
              <strong>{data.previous_window.article_count}</strong>
              <small>{formatDate(data.previous_window.start)} – {formatDate(data.previous_window.end)}</small>
            </div>
            <div className="regional-stat">
              <span>TOPICS TRACKED</span>
              <strong>{data.topics.length}</strong>
              <small>Ranked by recent coverage volume</small>
            </div>
            <div className="regional-stat">
              <span>COUNTRIES TRACKED</span>
              <strong>{data.countries.length}</strong>
              <small>Ranked by recent coverage volume</small>
            </div>
          </div>

          <section className="regional-panel trend-timeline-panel">
            <div className="regional-panel-heading">
              <h3>Publication activity</h3>
              <span>Daily article volume · latest 30 days of available data</span>
            </div>
            {data.timeline.length ? (
              <div className="trend-timeline">
                {data.timeline.map((item) => (
                  <div className="trend-day" key={item.date} title={`${formatDate(item.date)}: ${item.article_count} articles`}>
                    <strong>{item.article_count || ''}</strong>
                    <div className="trend-day-track">
                      <i style={{ height: `${(item.article_count / maxTimelineValue) * 100}%` }} />
                    </div>
                    <time>{formatDate(item.date).replace(/\s\d{4}$/, '')}</time>
                  </div>
                ))}
              </div>
            ) : (
              <p className="regional-empty">No dated publication activity found.</p>
            )}
          </section>

          <div className="regional-analysis-grid trend-analysis-grid">
            <TrendList
              title="Topic coverage shifts"
              items={data.topics}
              emptyMessage="No topic classifications are available in this period."
            />
            <TrendList
              title="Country coverage shifts"
              items={data.countries}
              emptyMessage="No recognised country coverage is available in this period."
            />
          </div>

          <div className="regional-analysis-grid trend-analysis-grid">
            <section className="regional-panel">
              <h3>Topics gaining attention</h3>
              {risingTopics.length ? risingTopics.slice(0, 6).map((item) => (
                <div className="trend-highlight-row" key={item.name}>
                  <span>{item.name}</span>
                  <strong>{item.status === 'new' ? 'NEW' : `+${item.change}`}</strong>
                </div>
              )) : (
                <p className="regional-empty">No topics increased in the selected comparison.</p>
              )}
            </section>
            <section className="regional-panel">
              <h3>Topics with lower coverage</h3>
              {decliningTopics.length ? decliningTopics.slice(0, 6).map((item) => (
                <div className="trend-highlight-row" key={item.name}>
                  <span>{item.name}</span>
                  <strong className="trend-declining">{item.change}</strong>
                </div>
              )) : (
                <p className="regional-empty">No topics declined in the selected comparison.</p>
              )}
            </section>
          </div>

          <p className="regional-data-note">
            METHODOLOGY — Trends compare the most recent {days}-day period ending
            on the latest publication date in the database with the immediately
            preceding {days}-day period. Counts represent articles, not event
            intensity or real-world frequency. A rise in coverage does not by
            itself confirm that a geopolitical situation has escalated.
          </p>
        </>
      )}
    </section>
  )
}

export default Trends
