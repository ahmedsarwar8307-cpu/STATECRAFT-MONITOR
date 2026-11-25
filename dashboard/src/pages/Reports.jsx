import { useEffect, useMemo, useState } from 'react'
import { FileText, Printer, RefreshCw } from 'lucide-react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Date unavailable'
  const date = new Date(value.includes('T') ? value : `${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-GB', {
    day: '2-digit', month: 'long', year: 'numeric',
  })
}

function Metric({ label, value, note }) {
  return (
    <div className="brief-metric">
      <span>{label}</span>
      <strong>{value}</strong>
      {note && <small>{note}</small>}
    </div>
  )
}

function Reports() {
  const [countries, setCountries] = useState([])
  const [country, setCountry] = useState('')
  const [days, setDays] = useState(30)
  const [brief, setBrief] = useState(null)
  const [loadingCountries, setLoadingCountries] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    async function loadCountries() {
      try {
        const response = await fetch(`${API_BASE}/api/countries`)
        if (!response.ok) throw new Error('Unable to load the country directory.')
        const data = await response.json()
        if (!active) return
        const available = (data.countries || []).map((item) => item.country)
        setCountries(available)
        if (available.length) setCountry(available[0])
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoadingCountries(false)
      }
    }
    loadCountries()
    return () => { active = false }
  }, [])

  const sortedCountries = useMemo(() => [...countries].sort((a, b) => a.localeCompare(b)), [countries])

  async function generateBrief(event) {
    event?.preventDefault()
    if (!country) return
    setGenerating(true)
    setError('')
    setBrief(null)
    try {
      const response = await fetch(
        `${API_BASE}/api/briefs/country/${encodeURIComponent(country)}?days=${days}`
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to generate this assessment.')

      // AI synthesis is an optional layer. Preserve the deterministic report
      // if Gemini is unavailable, rate-limited, or not configured.
      let aiResult = {
        available: false,
        detail: 'AI synthesis is not available. The evidence-based assessment below remains complete.',
      }
      try {
        const aiResponse = await fetch(
          `${API_BASE}/api/briefs/country/${encodeURIComponent(country)}/ai?days=${days}`
        )
        const aiData = await aiResponse.json()
        if (aiResponse.ok) {
          aiResult = aiData
        } else {
          aiResult.detail = aiData.detail || 'AI synthesis could not be generated.'
        }
      } catch {
        aiResult.detail = 'Could not connect to the AI service. The evidence-based report is still available.'
      }
      setBrief({ ...data, ai_assessment: aiResult })
    } catch (generateError) {
      setError(generateError.message)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <section className="page-section briefs-page">
      <span className="section-kicker">STRATEGIC PUBLICATIONS / EVIDENCE-LED ANALYSIS</span>
      <h1>Reports & Briefings</h1>
      <p>
        Generate structured country assessments from the platform's collected
        reporting. Each assessment links its observations to source headlines
        and makes the underlying data limitations explicit.
      </p>

      <form className="brief-builder no-print" onSubmit={generateBrief}>
        <div className="brief-builder-heading">
          <div>
            <span className="section-kicker">ASSESSMENT GENERATOR</span>
            <h2>Country Strategic Assessment</h2>
          </div>
          <FileText size={22} />
        </div>
        <div className="brief-builder-controls">
          <label>
            <span>SELECT COUNTRY</span>
            <select value={country} onChange={(event) => setCountry(event.target.value)} disabled={loadingCountries || !countries.length}>
              {sortedCountries.map((name) => <option key={name} value={name}>{name}</option>)}
            </select>
          </label>
          <label>
            <span>ANALYSIS PERIOD</span>
            <select value={days} onChange={(event) => setDays(Number(event.target.value))}>
              {[7, 14, 30, 60, 90].map((value) => <option key={value} value={value}>{value} days</option>)}
            </select>
          </label>
          <button className="brief-generate-button" type="submit" disabled={!country || generating || loadingCountries}>
            {generating ? <RefreshCw size={15} className="brief-spinning" /> : <FileText size={15} />}
            {generating ? 'GENERATING...' : 'GENERATE ASSESSMENT'}
          </button>
        </div>
        <small>Comparison uses the preceding equal-length period. Dates are anchored to the latest publication date recorded for the selected country.</small>
      </form>

      {loadingCountries && <div className="brief-status">Loading available countries...</div>}
      {error && <div className="brief-status brief-error">{error}</div>}
      {!brief && !generating && !error && (
        <div className="brief-empty">
          <FileText size={28} />
          <h3>Build an evidence-led country assessment</h3>
          <p>Select a country and analysis period, then generate a structured briefing with coverage comparisons, key topics, publisher distribution, event clusters and supporting headlines.</p>
        </div>
      )}
      {generating && <div className="brief-status">Compiling country coverage, topic comparisons, event clusters and source evidence...</div>}

      {brief && (
        <article className="strategic-brief" id="strategic-brief">
          <header className="brief-cover">
            <div className="brief-cover-top">
              <span>STATECRAFT MONITOR</span>
              <span>STRATEGIC INTELLIGENCE SERIES</span>
            </div>
            <div className="brief-cover-main">
              <span className="section-kicker">COUNTRY STRATEGIC ASSESSMENT</span>
              <h2>{brief.country}</h2>
              <p>Evidence-led media coverage assessment</p>
            </div>
            <div className="brief-cover-bottom">
              <span>PERIOD: {formatDate(brief.period.start)} — {formatDate(brief.period.end)}</span>
              <span>DATA THROUGH {formatDate(brief.data_through)}</span>
            </div>
          </header>

          <div className="brief-document-toolbar no-print">
            <span>ASSESSMENT GENERATED {formatDate(brief.generated_at)}</span>
            <button type="button" onClick={() => window.print()}><Printer size={14} /> PRINT / SAVE PDF</button>
          </div>

          <section className="brief-section brief-ai-section">
            <div className="brief-ai-heading">
              <div>
                <span className="section-kicker">AI-GENERATED STRATEGIC ASSESSMENT</span>
                <h3>Analytical assessment</h3>
              </div>
              <span className={brief.ai_assessment?.available ? 'brief-ai-status is-ready' : 'brief-ai-status'}>
                {brief.ai_assessment?.available ? 'GEMINI SYNTHESIS' : 'EVIDENCE-LED MODE'}
              </span>
            </div>
            {brief.ai_assessment?.available ? (
              <>
                <p className="brief-ai-intro">
                  AI-assisted interpretation of the collected headlines and metadata. Supporting headlines, publisher details and original-report links below provide the reader-facing evidence trail.
                </p>
                {[
                  ['Executive overview', brief.ai_assessment.assessment.executive_overview],
                  ['Major developments', brief.ai_assessment.assessment.major_developments],
                  ['Analytical observations', brief.ai_assessment.assessment.analytical_observations],
                  ['Potential implications', brief.ai_assessment.assessment.potential_implications],
                  ['Uncertainties & information gaps', brief.ai_assessment.assessment.uncertainties_information_gaps],
                ].map(([heading, items]) => (
                  <div className="brief-ai-subsection" key={heading}>
                    <h4>{heading}</h4>
                    <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
                  </div>
                ))}
                <small className="brief-caveat">
                  Generated by {brief.ai_assessment.provider} · Model {brief.ai_assessment.model} · {brief.ai_assessment.cached ? 'Reused cached assessment' : 'New synthesis'} · AI interpretation is not independent verification or a prediction.
                </small>
              </>
            ) : (
              <div className="brief-ai-unavailable">
                <p>{brief.ai_assessment?.detail || 'AI synthesis is currently unavailable.'}</p>
                <small>The structured evidence-based assessment and all supporting data sections remain available below. AI availability does not affect the underlying analysis.</small>
              </div>
            )}
          </section>

          <section className="brief-section">
            <span className="section-kicker">01 / EXECUTIVE COVERAGE SUMMARY</span>
            <h3>Reporting overview</h3>
            <p>
              During the selected {brief.period_days}-day period, the database recorded
              <strong> {brief.coverage_overview.recent_articles} articles</strong> associated
              with {brief.country}, from <strong>{brief.coverage_overview.recent_source_count} publishers</strong>.
              {brief.coverage_overview.previous_articles > 0
                ? ` This compares with ${brief.coverage_overview.previous_articles} articles in the preceding period, representing a ${Math.abs(brief.coverage_overview.change_percent)}% ${brief.coverage_overview.change_status} in recorded coverage.`
                : ' No articles were recorded in the preceding comparison period, so a percentage change cannot be calculated.'}
            </p>
            <div className="brief-metrics-grid">
              <Metric label="CURRENT PERIOD" value={brief.coverage_overview.recent_articles} note="Country-linked articles" />
              <Metric label="PREVIOUS PERIOD" value={brief.coverage_overview.previous_articles} note="Equal-length baseline" />
              <Metric label="PUBLISHERS" value={brief.coverage_overview.recent_source_count} note="In current period" />
              <Metric label="COVERAGE DEPTH" value={brief.coverage_overview.evidence_depth} note="Not a truth or risk score" />
            </div>
            <div className="brief-assessment-note">{brief.coverage_overview.evidence_note}</div>
          </section>

          <section className="brief-section">
            <span className="section-kicker">02 / THEMATIC COVERAGE</span>
            <h3>Topics and shifts in attention</h3>
            {brief.topic_analysis.length ? (
              <div className="brief-table-wrap">
                <table className="brief-table">
                  <thead><tr><th>Topic</th><th>Current</th><th>Previous</th><th>Change</th><th>Current share</th></tr></thead>
                  <tbody>{brief.topic_analysis.map((item) => (
                    <tr key={item.topic}>
                      <td>{item.topic}</td><td>{item.recent_articles}</td><td>{item.previous_articles}</td>
                      <td>{item.change > 0 ? '+' : ''}{item.change} · {item.status}</td>
                      <td>{item.recent_share_percent}%</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            ) : <p>No classified topics were recorded in the selected period.</p>}
          </section>

          <section className="brief-section">
            <span className="section-kicker">03 / PUBLISHER DISTRIBUTION</span>
            <h3>Sources represented</h3>
            {brief.source_distribution.length ? (
              <div className="brief-source-list">{brief.source_distribution.map((item) => (
                <div key={item.source}><span>{item.source}</span><strong>{item.article_count} articles</strong></div>
              ))}</div>
            ) : <p>No publisher information was recorded for this period.</p>}
          </section>

          <section className="brief-section">
            <span className="section-kicker">04 / EVENT COVERAGE</span>
            <h3>Events reported by multiple publishers</h3>
            {brief.multi_publisher_event_coverage.length ? brief.multi_publisher_event_coverage.map((event, index) => (
              <div className="brief-event" key={`${event.headline}-${index}`}>
                <h4>{event.headline}</h4>
                <p>{event.article_count} related articles · {event.source_count} publisher names · {formatDate(event.first_seen)} to {formatDate(event.latest_seen)}</p>
                <div className="brief-source-tags">{event.sources.map((source) => <span key={source}>{source}</span>)}</div>
                {event.articles.map((article) => (
                  <div className="brief-evidence-row" key={article.id}>
                    <strong>{article.title}</strong>
                    <small>{article.source} · {formatDate(article.published)}</small>
                    {article.link && <a href={article.link} target="_blank" rel="noreferrer">Open original report ↗</a>}
                  </div>
                ))}
              </div>
            )) : <p>No candidate event clusters met the multi-publisher threshold in this period.</p>}
            <small className="brief-caveat">Publisher overlap indicates shared coverage only. It does not independently verify the claims in the reports.</small>
          </section>

          <section className="brief-section">
            <span className="section-kicker">05 / COVERAGE TIMELINE</span>
            <h3>Daily reporting volume</h3>
            <div className="brief-timeline">
              {brief.coverage_timeline.map((item) => {
                const max = Math.max(1, ...brief.coverage_timeline.map((entry) => entry.article_count))
                return <div key={item.date} title={`${formatDate(item.date)}: ${item.article_count} articles`}>
                  <strong>{item.article_count || ''}</strong><i style={{ height: `${item.article_count ? (item.article_count / max) * 100 : 0}%` }} />
                  <small>{formatDate(item.date).slice(0, 6)}</small>
                </div>
              })}
            </div>
          </section>

          <section className="brief-section">
            <span className="section-kicker">06 / KEY SOURCE HEADLINES</span>
            <h3>Supporting reporting</h3>
            {brief.key_headlines.length ? brief.key_headlines.map((article) => (
              <div className="brief-evidence-row" key={article.id}>
                <strong>{article.title}</strong>
                <small>{article.source || 'Unknown publisher'} · {formatDate(article.published)}{article.topics.length ? ` · ${article.topics.join(', ')}` : ''}</small>
                {article.link && <a href={article.link} target="_blank" rel="noreferrer">Read original report ↗</a>}
              </div>
            )) : <p>No headlines were recorded in the selected period.</p>}
          </section>

          <section className="brief-section">
            <span className="section-kicker">07 / METHODOLOGY & LIMITATIONS</span>
            <h3>How to interpret this assessment</h3>
            <ul className="brief-limitations">{brief.data_quality.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
            <p className="brief-footnote">
              The supporting sections are a structured compilation of collected headlines and metadata. AI-generated interpretation, when available, is not a fact-check verdict, a national risk rating or a substitute for reading the original reports.
            </p>
            <p className="brief-generated-note">
              Prepared by STATECRAFT MONITOR · Generated {formatDate(brief.generated_at)} · {brief.data_quality.dated_country_articles} dated country-linked records available overall · {brief.data_quality.undated_country_articles} undated records excluded from period comparisons.
            </p>
          </section>
        </article>
      )}
    </section>
  )
}

export default Reports
