import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

function SignalCard({ signal }) {
  return (
    <article className="signal-card">
      <div className="signal-card-top">
        <span className="signal-type">{signal.label}</span>
        <span className={`signal-state ${signal.status}`}>
          {signal.status.replaceAll('_', ' ')}
        </span>
      </div>
      <h3>{signal.name}</h3>
      <p>{signal.interpretation}</p>
      <div className="signal-metrics">
        <span><strong>{signal.recent_mentions}</strong> recent articles</span>
        {signal.previous_mentions !== null && signal.previous_mentions !== undefined && (
          <span><strong>{signal.previous_mentions}</strong> previous articles</span>
        )}
        <span><strong>{signal.source_count}</strong> publishers</span>
        {signal.change_percent !== null && signal.change_percent !== undefined && (
          <span><strong>{signal.change_percent > 0 ? '+' : ''}{signal.change_percent}%</strong> coverage change</span>
        )}
      </div>
      {signal.sources?.length > 0 && (
        <div className="signal-source-list">
          {signal.sources.map((source) => <span key={source}>{source}</span>)}
        </div>
      )}
      {signal.countries?.length > 0 && (
        <p>Countries: {signal.countries.join(' · ')}</p>
      )}
      {signal.topics?.length > 0 && (
        <p>Topics: {signal.topics.join(' · ')}</p>
      )}
      {signal.articles?.length > 0 && (
        <details className="signal-evidence">
          <summary>Inspect supporting headlines ({signal.articles.length})</summary>
          {signal.articles.map((article) => (
            <article key={article.id}>
              <strong>{article.title}</strong>
              <small>{article.source || 'Unknown publisher'} · {formatDate(article.published)}</small>
              {article.link && <a href={article.link} target="_blank" rel="noreferrer">Open original report ↗</a>}
            </article>
          ))}
        </details>
      )}
    </article>
  )
}

function StrategicSignals() {
  const [days, setDays] = useState(14)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function loadSignals() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`${API_BASE}/api/strategic-signals?days=${days}`)
        if (!response.ok) throw new Error('Unable to retrieve strategic coverage signals.')
        const result = await response.json()
        if (active) setData(result)
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    loadSignals()
    return () => { active = false }
  }, [days])

  const groupedSignals = useMemo(() => {
    if (!data?.signals) return []
    return [
      { title: 'Multi-source event coverage', type: 'multi_source_event' },
      { title: 'Country coverage shifts', type: 'country_shift' },
      { title: 'Topic coverage shifts', type: 'topic_shift' },
    ].map((group) => ({
      ...group,
      items: data.signals.filter((signal) => signal.type === group.type),
    })).filter((group) => group.items.length)
  }, [data])

  return (
    <section className="page-section regional-page signals-page">
      <span className="section-kicker">INTELLIGENCE MONITORING / COVERAGE-BASED INDICATORS</span>
      <h1>Strategic Signals</h1>
      <p>
        Identify notable shifts in geopolitical news coverage, emerging areas of
        attention and events appearing across multiple publishers. Every signal
        links back to the headlines used to detect it.
      </p>

      <div className="signal-controls">
        <div>
          <span className="section-kicker">COMPARISON WINDOW</span>
          <strong>{days} days compared with the preceding {days} days</strong>
        </div>
        <div className="trend-window-buttons" aria-label="Choose signal comparison window">
          {[7, 14, 30].map((value) => (
            <button type="button" key={value} className={days === value ? 'active' : ''} onClick={() => setDays(value)}>
              {value}D
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="regional-status">Analysing country, topic and event coverage...</div>}
      {!loading && error && <div className="regional-status regional-error">{error} Make sure the backend is running.</div>}
      {!loading && data && !data.available && <div className="regional-status">{data.message}</div>}

      {!loading && data?.available && (
        <>
          <div className="signal-period">
            <span>DATA THROUGH <strong>{formatDate(data.latest_data_date)}</strong></span>
            <span>{data.articles_analysed} DATED ARTICLES IN DATABASE</span>
          </div>

          <div className="signal-summary">
            <div className="regional-stat"><span>TOTAL SIGNALS</span><strong>{data.summary.total_signals}</strong><small>Coverage indicators detected</small></div>
            <div className="regional-stat"><span>COUNTRY SHIFTS</span><strong>{data.summary.country_shifts}</strong><small>Notable changes in country attention</small></div>
            <div className="regional-stat"><span>TOPIC SHIFTS</span><strong>{data.summary.topic_shifts}</strong><small>Notable changes in topic attention</small></div>
            <div className="regional-stat"><span>MULTI-SOURCE EVENTS</span><strong>{data.summary.multi_source_events}</strong><small>Candidate clusters across publishers</small></div>
          </div>

          <div className="signal-period">
            <span>RECENT: <strong>{formatDate(data.recent_period.start)} – {formatDate(data.recent_period.end)}</strong> · {data.recent_period.article_count} articles</span>
            <span>PREVIOUS: <strong>{formatDate(data.previous_period.start)} – {formatDate(data.previous_period.end)}</strong> · {data.previous_period.article_count} articles</span>
          </div>

          {groupedSignals.length ? groupedSignals.map((group) => (
            <section key={group.type} className="regional-panel" style={{ marginBottom: 14 }}>
              <div className="regional-panel-heading">
                <h3>{group.title}</h3>
                <span>{group.items.length} detected</span>
              </div>
              <div className="signal-grid">
                {group.items.map((signal) => <SignalCard key={signal.id} signal={signal} />)}
              </div>
            </section>
          )) : (
            <div className="regional-status">
              No signals met the current detection thresholds. This does not mean no important events are occurring; it means the available dataset did not produce a qualifying coverage pattern.
            </div>
          )}

          <div className="signal-methodology">
            <strong>HOW TO READ THESE SIGNALS</strong><br />
            {data.methodology}<br /><br />
            A rise in coverage can reflect editorial attention, source availability or a developing story. Multiple publishers reporting the same event does not independently verify every factual claim. Signal counts are not measures of geopolitical severity, credibility scores or predictions.
          </div>
        </>
      )}
    </section>
  )
}

export default StrategicSignals
