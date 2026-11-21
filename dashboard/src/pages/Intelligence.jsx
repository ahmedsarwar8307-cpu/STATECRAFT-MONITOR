import { useEffect, useMemo, useState } from 'react'

const API_BASE = 'http://127.0.0.1:8000'

function formatDate(value) {
  if (!value) return 'Date unavailable'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function Intelligence() {
  const [overview, setOverview] = useState(null)
  const [selectedRegion, setSelectedRegion] = useState('')
  const [details, setDetails] = useState(null)
  const [loadingOverview, setLoadingOverview] = useState(true)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [error, setError] = useState('')
  const [relations, setRelations] = useState(null)
  const [selectedPair, setSelectedPair] = useState(null)
  const [pairDetails, setPairDetails] = useState(null)
  const [loadingRelations, setLoadingRelations] = useState(true)
  const [loadingPair, setLoadingPair] = useState(false)
  const [relationError, setRelationError] = useState('')

  useEffect(() => {
    let active = true

    async function loadRegions() {
      try {
        const response = await fetch(`${API_BASE}/api/regions`)
        if (!response.ok) throw new Error('Unable to retrieve regional coverage.')

        const data = await response.json()
        if (!active) return

        setOverview(data)
        const firstCoveredRegion = data.regions.find(
          (region) => region.article_count > 0
        )
        if (firstCoveredRegion) setSelectedRegion(firstCoveredRegion.region)
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoadingOverview(false)
      }
    }

    loadRegions()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!selectedRegion) {
      setDetails(null)
      return undefined
    }

    let active = true

    async function loadRegionDetails() {
      setLoadingDetails(true)
      setError('')

      try {
        const response = await fetch(
          `${API_BASE}/api/regions/${encodeURIComponent(selectedRegion)}`
        )
        if (!response.ok) throw new Error('Unable to retrieve this region\'s analysis.')

        const data = await response.json()
        if (active) setDetails(data)
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoadingDetails(false)
      }
    }

    loadRegionDetails()

    return () => {
      active = false
    }
  }, [selectedRegion])

  useEffect(() => {
    let active = true

    async function loadRelations() {
      try {
        const response = await fetch(`${API_BASE}/api/country-relations?limit=50`)
        if (!response.ok) throw new Error('Unable to retrieve country relationship analysis.')

        const data = await response.json()
        if (!active) return

        setRelations(data)
        if (data.pairs.length) {
          setSelectedPair({
            country_a: data.pairs[0].country_a,
            country_b: data.pairs[0].country_b,
          })
        }
      } catch (loadError) {
        if (active) setRelationError(loadError.message)
      } finally {
        if (active) setLoadingRelations(false)
      }
    }

    loadRelations()
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!selectedPair) {
      setPairDetails(null)
      return undefined
    }

    let active = true

    async function loadPairDetails() {
      setLoadingPair(true)
      setRelationError('')

      try {
        const params = new URLSearchParams(selectedPair)
        const response = await fetch(`${API_BASE}/api/country-relations/pair?${params}`)
        if (!response.ok) throw new Error('Unable to retrieve this country pair.')

        const data = await response.json()
        if (active) setPairDetails(data)
      } catch (loadError) {
        if (active) setRelationError(loadError.message)
      } finally {
        if (active) setLoadingPair(false)
      }
    }

    loadPairDetails()
    return () => { active = false }
  }, [selectedPair])

  const maxTimelineValue = useMemo(() => {
    if (!details?.coverage_timeline?.length) return 1
    return Math.max(...details.coverage_timeline.map((item) => item.article_count), 1)
  }, [details])

  const maxCountryValue = useMemo(() => {
    if (!details?.countries?.length) return 1
    return Math.max(...details.countries.map((item) => item.article_count), 1)
  }, [details])

  const maxTopicValue = useMemo(() => {
    if (!details?.topics?.length) return 1
    return Math.max(...details.topics.map((item) => item.article_count), 1)
  }, [details])

  return (
    <section className="page-section regional-page">
      <span className="section-kicker">GEOGRAPHIC INTELLIGENCE / REGIONAL ANALYSIS</span>
      <h1>Regional Intelligence</h1>
      <p>
        Examine how the current news dataset covers world regions, which countries
        are represented, and which geopolitical topics appear most frequently.
      </p>

      {loadingOverview && (
        <div className="regional-status">Loading regional coverage from the database...</div>
      )}

      {!loadingOverview && error && !overview && (
        <div className="regional-status regional-error">
          {error} Make sure the FastAPI backend is running.
        </div>
      )}

      {overview && (
        <>
          <div className="regional-overview">
            <div className="regional-stat">
              <span>REGIONS INDEXED</span>
              <strong>{overview.region_count}</strong>
              <small>Defined geographic groupings</small>
            </div>
            <div className="regional-stat">
              <span>REGIONS WITH COVERAGE</span>
              <strong>{overview.regions_with_coverage}</strong>
              <small>At least one matching article</small>
            </div>
          </div>

          <div className="regional-section-heading">
            <div>
              <span className="section-kicker">REGIONAL DIRECTORY</span>
              <h2>Coverage by region</h2>
            </div>
            <span>{overview.regions_with_coverage} regions currently represented</span>
          </div>

          <div className="regional-grid">
            {overview.regions.map((region) => (
              <button
                type="button"
                key={region.region}
                className={`regional-card ${selectedRegion === region.region ? 'selected' : ''}`}
                onClick={() => setSelectedRegion(region.region)}
              >
                <span className="regional-card-top">
                  <strong>{region.region}</strong>
                  <span>{region.article_count} articles</span>
                </span>
                <span className="regional-card-metrics">
                  {region.country_count} countries · {region.source_count} sources
                </span>
                {region.top_topics.length > 0 ? (
                  <span className="regional-card-topics">
                    {region.top_topics.map((topic) => topic.topic).join(' · ')}
                  </span>
                ) : (
                  <span className="regional-card-topics">No matching articles in this dataset</span>
                )}
                <span className="regional-card-action">
                  {selectedRegion === region.region ? 'VIEWING REGION' : 'VIEW ANALYSIS'}
                </span>
              </button>
            ))}
          </div>

          {selectedRegion && (
            <div className="regional-detail">
              {loadingDetails && (
                <div className="regional-status">Loading {selectedRegion} analysis...</div>
              )}

              {!loadingDetails && error && (
                <div className="regional-status regional-error">{error}</div>
              )}

              {!loadingDetails && details && (
                <>
                  <div className="regional-detail-header">
                    <div>
                      <span className="section-kicker">REGIONAL INTELLIGENCE PROFILE</span>
                      <h2>{details.region}</h2>
                      <p>
                        Analysis of articles tagged with one or more countries assigned
                        to this region. An article is counted once within a region.
                      </p>
                    </div>
                    <span className="regional-record-count">
                      {details.article_count} matching articles
                    </span>
                  </div>

                  <div className="regional-detail-stats">
                    <div><span>ARTICLES</span><strong>{details.article_count}</strong></div>
                    <div><span>COUNTRIES</span><strong>{details.country_count}</strong></div>
                    <div><span>NEWS SOURCES</span><strong>{details.source_count}</strong></div>
                    <div><span>TOPICS</span><strong>{details.topic_count}</strong></div>
                  </div>

                  <div className="regional-analysis-grid">
                    <div className="regional-panel">
                      <h3>Country coverage</h3>
                      {details.countries.length ? details.countries.map((item) => (
                        <div className="regional-ranking-row" key={item.country}>
                          <span>{item.country}</span>
                          <div className="regional-ranking-track">
                            <i style={{ width: `${(item.article_count / maxCountryValue) * 100}%` }} />
                          </div>
                          <strong>{item.article_count}</strong>
                        </div>
                      )) : <p className="regional-empty">No country coverage recorded.</p>}
                    </div>

                    <div className="regional-panel">
                      <h3>Topic distribution</h3>
                      {details.topics.length ? details.topics.map((item) => (
                        <div className="regional-ranking-row" key={item.topic}>
                          <span>{item.topic}</span>
                          <div className="regional-ranking-track">
                            <i style={{ width: `${(item.article_count / maxTopicValue) * 100}%` }} />
                          </div>
                          <strong>{item.article_count}</strong>
                        </div>
                      )) : <p className="regional-empty">No topic data recorded.</p>}
                    </div>
                  </div>

                  <div className="regional-panel regional-timeline">
                    <div className="regional-panel-heading">
                      <h3>Coverage timeline</h3>
                      <span>Articles by publication date</span>
                    </div>
                    {details.coverage_timeline.length ? (
                      <div className="regional-timeline-chart">
                        {details.coverage_timeline.map((item) => (
                          <div className="regional-timeline-column" key={item.date}>
                            <strong>{item.article_count}</strong>
                            <div className="regional-timeline-track">
                              <i style={{ height: `${(item.article_count / maxTimelineValue) * 100}%` }} />
                            </div>
                            <time>{formatDate(item.date)}</time>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="regional-empty">No usable publication dates are available.</p>
                    )}
                  </div>

                  <div className="regional-panel regional-sources">
                    <h3>Source distribution</h3>
                    <div className="regional-source-list">
                      {details.sources.map((item) => (
                        <div className="regional-source-item" key={item.source}>
                          <span>{item.source}</span>
                          <strong>{item.article_count} articles</strong>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="regional-panel regional-articles">
                    <div className="regional-panel-heading">
                      <h3>Articles in this region</h3>
                      <span>{details.articles.length} records</span>
                    </div>
                    {details.articles.map((article) => (
                      <article className="regional-article" key={article.id}>
                        <div className="regional-article-meta">
                          <span>{article.source || 'Unknown source'}</span>
                          <time>{formatDate(article.published)}</time>
                        </div>
                        <h4>{article.title}</h4>
                        <div className="regional-article-tags">
                          {article.region_countries.map((country) => (
                            <span key={country}>{country}</span>
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
                    {!details.articles.length && (
                      <p className="regional-empty">No articles currently match this region.</p>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
          <section className="relationship-section">
            <div className="regional-section-heading">
              <div>
                <span className="section-kicker">COUNTRY-TO-COUNTRY INTELLIGENCE</span>
                <h2>Shared news coverage</h2>
              </div>
              <span>Country co-mentions across articles</span>
            </div>

            {loadingRelations && (
              <div className="regional-status">Analysing country pairs in the database...</div>
            )}

            {!loadingRelations && relationError && !relations && (
              <div className="regional-status regional-error">{relationError}</div>
            )}

            {relations && (
              <>
                <div className="regional-overview relationship-overview">
                  <div className="regional-stat">
                    <span>COUNTRIES WITH SHARED COVERAGE</span>
                    <strong>{relations.countries_with_shared_coverage}</strong>
                    <small>Countries appearing alongside at least one other country</small>
                  </div>
                  <div className="regional-stat">
                    <span>COUNTRY PAIRS IDENTIFIED</span>
                    <strong>{relations.total_pairs}</strong>
                    <small>Distinct pairs found in shared articles</small>
                  </div>
                  <div className="regional-stat">
                    <span>ARTICLES WITH MULTIPLE COUNTRIES</span>
                    <strong>{relations.articles_with_multiple_countries}</strong>
                    <small>Articles containing two or more recognised countries</small>
                  </div>
                </div>

                <div className="relationship-workspace">
                  <div className="regional-panel relationship-directory">
                    <div className="regional-panel-heading">
                      <h3>Most-covered country pairs</h3>
                      <span>Top {relations.pairs.length}</span>
                    </div>
                    {relations.pairs.map((pair) => {
                      const isSelected = selectedPair?.country_a === pair.country_a &&
                        selectedPair?.country_b === pair.country_b
                      return (
                        <button
                          type="button"
                          key={`${pair.country_a}|${pair.country_b}`}
                          className={`relationship-pair ${isSelected ? 'selected' : ''}`}
                          onClick={() => setSelectedPair({
                            country_a: pair.country_a,
                            country_b: pair.country_b,
                          })}
                        >
                          <span className="relationship-pair-names">
                            <strong>{pair.country_a}</strong>
                            <span>↔</span>
                            <strong>{pair.country_b}</strong>
                          </span>
                          <span className="relationship-pair-meta">
                            {pair.article_count} shared articles · {pair.topic_count} topics
                          </span>
                        </button>
                      )
                    })}
                    {!relations.pairs.length && (
                      <p className="regional-empty">
                        No articles currently mention more than one recognised country.
                      </p>
                    )}
                  </div>

                  <div className="regional-panel relationship-profile">
                    {loadingPair && (
                      <div className="regional-status">Loading country-pair analysis...</div>
                    )}
                    {!loadingPair && relationError && (
                      <div className="regional-status regional-error">{relationError}</div>
                    )}
                    {!loadingPair && pairDetails && (
                      <>
                        <span className="section-kicker">SHARED COVERAGE PROFILE</span>
                        <h3 className="relationship-profile-title">
                          {pairDetails.country_a} <span>↔</span> {pairDetails.country_b}
                        </h3>
                        <p className="relationship-description">
                          These countries were both identified in the articles below.
                          This indicates shared news coverage, not necessarily a direct
                          political, diplomatic, or security relationship.
                        </p>
                        <div className="regional-detail-stats relationship-detail-stats">
                          <div><span>SHARED ARTICLES</span><strong>{pairDetails.article_count}</strong></div>
                          <div><span>TOPICS</span><strong>{pairDetails.topic_count}</strong></div>
                          <div><span>SOURCES</span><strong>{pairDetails.source_count}</strong></div>
                        </div>

                        <h4 className="relationship-subheading">Shared topic distribution</h4>
                        {pairDetails.topics.map((item) => (
                          <div className="regional-ranking-row" key={item.topic}>
                            <span>{item.topic}</span>
                            <span className="relationship-topic-count">
                              {item.article_count} articles
                            </span>
                          </div>
                        ))}

                        <h4 className="relationship-subheading">News sources</h4>
                        <div className="regional-source-list">
                          {pairDetails.sources.map((item) => (
                            <div className="regional-source-item" key={item.source}>
                              <span>{item.source}</span>
                              <strong>{item.article_count} articles</strong>
                            </div>
                          ))}
                        </div>

                        <h4 className="relationship-subheading">Articles mentioning both countries</h4>
                        {pairDetails.articles.map((article) => (
                          <article className="regional-article" key={article.id}>
                            <div className="regional-article-meta">
                              <span>{article.source || 'Unknown source'}</span>
                              <time>{formatDate(article.published)}</time>
                            </div>
                            <h4>{article.title}</h4>
                            <div className="regional-article-tags">
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
                    )}
                    {!loadingPair && !pairDetails && !relationError && (
                      <p className="regional-empty">Select a country pair to inspect its shared coverage.</p>
                    )}
                  </div>
                </div>
              </>
            )}
            <p className="regional-data-note">
              METHODOLOGY — A pair is counted once per article when both country names
              appear in that article's recognised country list. Co-mention is not proof
              of cooperation, conflict, or a formal relationship.
            </p>
          </section>

          <p className="regional-data-note">
            DATA NOTE — Regional totals reflect the current STATECRAFT MONITOR database
            and country-recognition results. They are not a measure of total real-world
            news activity or comprehensive regional coverage.
          </p>
        </>
      )}
    </section>
  )
}

export default Intelligence
