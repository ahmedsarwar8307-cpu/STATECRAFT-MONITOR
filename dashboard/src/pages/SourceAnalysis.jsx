import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Not recorded'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function statusLabel(status) {
  if (status === 'ok') return 'OPERATIONAL'
  if (status === 'partial') return 'PARTIAL'
  if (status === 'not_recorded') return 'NO HISTORY'
  if (status === 'empty') return 'EMPTY FEED'
  return 'FAILED'
}

function SourceAnalysis() {
  const [runs, setRuns] = useState(30)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(API_BASE + '/api/source-health?runs=' + runs)
        if (!response.ok) throw new Error('Unable to retrieve source analysis.')
        const result = await response.json()
        if (active) setData(result)
      } catch (err) {
        if (active) setError(err.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [runs])

  const sortedByArticles = useMemo(
    () => [...(data?.sources ?? [])].sort((a, b) => b.database_articles - a.database_articles),
    [data]
  )
  const totalSourceArticles = useMemo(
    () => sortedByArticles.reduce((sum, item) => sum + item.database_articles, 0),
    [sortedByArticles]
  )

  return (
    <section className="page-section regional-page source-analysis-page">
      <span className="section-kicker">SYSTEM INTELLIGENCE / SOURCE MONITORING</span>
      <h1>Source Reliability & Coverage</h1>
      <p>
        Assess publisher collection reliability, contribution to the article
        database, and the geographic and thematic range represented in each
        source’s reporting.
      </p>

      <div className="trend-controls">
        <div>
          <span className="section-kicker">RELIABILITY HISTORY</span>
          <strong>Latest {runs} collection runs</strong>
        </div>
        <div className="trend-window-buttons" aria-label="Choose collection history window">
          {[7, 30, 90, 365].map((value) => (
            <button type="button" key={value} className={runs === value ? 'active' : ''} onClick={() => setRuns(value)}>
              {value}R
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="regional-status">Analysing collection history and publisher coverage...</div>}
      {!loading && error && <div className="regional-status regional-error">{error} Make sure the FastAPI backend is running.</div>}
      {!loading && data && !data.available && (
        <div className="regional-status">
          {data.message}
          <p className="source-analysis-hint">The history file is created automatically the next time you run <code>python src/news_collector.py</code>.</p>
        </div>
      )}

      {!loading && data?.available && (
        <>
          <div className="source-analysis-period">
            <span>LAST RECORDED COLLECTION <strong>{formatDate(data.latest_run?.collected_at)}</strong></span>
            <span>{data.runs_recorded} RUN{data.runs_recorded === 1 ? '' : 'S'} IN SELECTED HISTORY</span>
          </div>

          <div className="regional-overview trend-overview">
            <div className="regional-stat"><span>RECENT SOURCE SUCCESS</span><strong>{data.recent_success_rate ?? '—'}{data.recent_success_rate == null ? '' : '%'}</strong><small>Across recorded source checks</small></div>
            <div className="regional-stat"><span>WORKING SOURCES · LATEST</span><strong>{data.successful_sources_latest}/{data.configured_sources}</strong><small>Valid articles returned</small></div>
            <div className="regional-stat"><span>FAILED / EMPTY · LATEST</span><strong>{data.failed_sources_latest}</strong><small>Sources needing attention</small></div>
            <div className="regional-stat"><span>DATABASE ARTICLES</span><strong>{data.database_article_count}</strong><small>Across all retained records</small></div>
          </div>

          <section className="regional-panel source-health-panel">
            <div className="regional-panel-heading"><h3>Publisher reliability</h3><span>Success means a feed returned valid articles</span></div>
            <div className="source-health-table-wrap">
              <table className="source-health-table">
                <thead><tr><th>Publisher</th><th>Success rate</th><th>Successful runs</th><th>Articles collected</th><th>Latest status</th></tr></thead>
                <tbody>
                  {data.sources.map((source) => (
                    <tr key={source.source}>
                      <td><strong>{source.source}</strong><small>{source.observations ? source.observations + ' recorded checks' : 'Awaiting first run'}</small></td>
                      <td>{source.success_rate == null ? '—' : <div className="source-rate-cell"><strong>{source.success_rate}%</strong><div className="source-rate-track"><i style={{ width: source.success_rate + '%' }} /></div></div>}</td>
                      <td>{source.successful_runs}/{source.observations || '—'}</td>
                      <td>{source.articles_collected}</td>
                      <td><span className={'source-status source-' + source.latest_status}>{statusLabel(source.latest_status)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="regional-panel source-contribution-panel">
            <div className="regional-panel-heading"><h3>Database contribution</h3><span>Retained articles grouped by publisher</span></div>
            {sortedByArticles.map((source) => (
              <div className="source-contribution-row" key={source.source}>
                <div><strong>{source.source}</strong><span>{source.database_articles} articles · {source.top_countries.length} countries · {source.top_topics.length} topics represented</span></div>
                <div className="source-contribution-track"><i style={{ width: (totalSourceArticles ? source.database_articles / totalSourceArticles * 100 : 0) + '%' }} /></div>
                <strong>{totalSourceArticles ? (source.database_articles / totalSourceArticles * 100).toFixed(1) : '0.0'}%</strong>
              </div>
            ))}
          </section>

          <div className="source-coverage-grid">
            {sortedByArticles.map((source) => (
              <section className="regional-panel source-coverage-card" key={source.source}>
                <div className="regional-panel-heading"><h3>{source.source}</h3><span>{source.database_articles} database articles</span></div>
                <div className="source-coverage-columns">
                  <div><strong>COUNTRY COVERAGE</strong>
                    {source.top_countries.length ? source.top_countries.map((item) => <div className="source-coverage-item" key={item.name}><span>{item.name}</span><b>{item.article_count}</b></div>) : <small>No country tags recorded</small>}
                  </div>
                  <div><strong>TOPIC COVERAGE</strong>
                    {source.top_topics.length ? source.top_topics.map((item) => <div className="source-coverage-item" key={item.name}><span>{item.name}</span><b>{item.article_count}</b></div>) : <small>No topic tags recorded</small>}
                  </div>
                </div>
                {source.latest_error && <p className="source-latest-error">LATEST COLLECTION ERROR: {source.latest_error}</p>}
              </section>
            ))}
          </div>

          <p className="regional-data-note">
            METHODOLOGY — Reliability is calculated from recorded collection runs, not publisher trustworthiness or factual accuracy. Database contribution counts retained articles, while country and topic figures reflect detected tags in those articles. These measures describe the platform’s collected media coverage, not the completeness of global reporting or the importance of real-world events.
          </p>
        </>
      )}
    </section>
  )
}

export default SourceAnalysis
