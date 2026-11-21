
import { useEffect, useMemo, useState } from 'react'
import {
  ExternalLink,
  Newspaper,
  Search,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

function WorldNews() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTopic, setSelectedTopic] = useState('All topics')
  const [selectedCountry, setSelectedCountry] = useState('All countries')
  const [selectedSource, setSelectedSource] = useState('All sources')
  const [sortOrder, setSortOrder] = useState('newest')
  const [currentPage, setCurrentPage] = useState(1)

  const articlesPerPage = 16

  // FETCH ARTICLES FROM FASTAPI
  useEffect(() => {
    async function fetchArticles() {
      try {
        const response = await fetch(
          'http://127.0.0.1:8000/api/articles'
        )

        if (!response.ok) {
          throw new Error('Unable to retrieve news articles.')
        }

        const data = await response.json()
        setArticles(data.articles)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchArticles()
  }, [])

  // GENERATE FILTER OPTIONS
  const topics = useMemo(() => {
    return [...new Set(
      articles.flatMap(article =>
        (article.topics || '')
          .split(',')
          .map(item => item.trim())
          .filter(Boolean)
      )
    )].sort()
  }, [articles])

  const countries = useMemo(() => {
    return [...new Set(
      articles.flatMap(article =>
        (article.countries || '')
          .split(',')
          .map(item => item.trim())
          .filter(item => item && item !== 'Unknown')
      )
    )].sort()
  }, [articles])

  const sources = useMemo(() => {
    return [...new Set(
      articles.map(article => article.source)
    )].sort()
  }, [articles])

  // FILTER ARTICLES
  const filteredArticles = useMemo(() => {
    return articles.filter(article => {
      const search = searchTerm.toLowerCase()

    const matchesSearch =
  (article.title || '').toLowerCase().includes(search) ||
  (article.source || '').toLowerCase().includes(search) ||
  (article.countries || '').toLowerCase().includes(search) ||
  (article.topics || '').toLowerCase().includes(search)

      const articleTopics = (article.topics || '')
        .split(',')
        .map(item => item.trim())

      const articleCountries = (article.countries || '')
        .split(',')
        .map(item => item.trim())

      const matchesTopic =
        selectedTopic === 'All topics' ||
        articleTopics.includes(selectedTopic)

      const matchesCountry =
        selectedCountry === 'All countries' ||
        articleCountries.includes(selectedCountry)

      const matchesSource =
        selectedSource === 'All sources' ||
        article.source === selectedSource

      return (
        matchesSearch &&
        matchesTopic &&
        matchesCountry &&
        matchesSource
      )
    })
  }, [
    articles,
    searchTerm,
    selectedTopic,
    selectedCountry,
    selectedSource,
  ])

  // SORT ARTICLES
  const sortedArticles = useMemo(() => {
    return [...filteredArticles].sort((a, b) => {
      const dateA = Date.parse(a.published) || 0
      const dateB = Date.parse(b.published) || 0

      return sortOrder === 'newest'
        ? dateB - dateA
        : dateA - dateB
    })
  }, [filteredArticles, sortOrder])

  // PAGINATION
  const totalPages = Math.ceil(
    sortedArticles.length / articlesPerPage
  )

  const startIndex = (currentPage - 1) * articlesPerPage

  const paginatedArticles = sortedArticles.slice(
    startIndex,
    startIndex + articlesPerPage
  )

  // RESET PAGE WHEN FILTERS OR SORTING CHANGE
  useEffect(() => {
    setCurrentPage(1)
  }, [
    searchTerm,
    selectedTopic,
    selectedCountry,
    selectedSource,
    sortOrder,
  ])

  // RESET ALL CONTROLS
  function resetFilters() {
    setSearchTerm('')
    setSelectedTopic('All topics')
    setSelectedCountry('All countries')
    setSelectedSource('All sources')
    setSortOrder('newest')
    setCurrentPage(1)
  }

  const filtersActive =
    searchTerm !== '' ||
    selectedTopic !== 'All topics' ||
    selectedCountry !== 'All countries' ||
    selectedSource !== 'All sources' ||
    sortOrder !== 'newest'

  // PAGE NAVIGATION
  function goToPreviousPage() {
    setCurrentPage(page => Math.max(page - 1, 1))
  }

  function goToNextPage() {
    setCurrentPage(page => Math.min(page + 1, totalPages))
  }

  return (
    <section className="page-section news-page">
      <span className="section-kicker">GLOBAL COVERAGE</span>
      <h1>World News</h1>
      <p>
        Developments shaping international affairs, diplomacy
        and global security.
      </p>

      <div className="news-feed-header">
        <div>
          <span className="section-kicker">LATEST REPORTING</span>
          <h2>Global news feed</h2>
        </div>

      </div>

      {/* SEARCH AND FILTER CONTROLS */}
      <div className="news-controls">
        <div className="news-search">
          <Search size={17} />
          <input
            type="text"
            placeholder="Search headlines, countries, topics or sources..."
            value={searchTerm}
            onChange={event => setSearchTerm(event.target.value)}
          />
        </div>

        <div className="news-filter-row">
          <select
            value={selectedTopic}
            onChange={event => setSelectedTopic(event.target.value)}
          >
            <option>All topics</option>
            {topics.map(topic => (
              <option key={topic} value={topic}>
                {topic}
              </option>
            ))}
          </select>

          <select
            value={selectedCountry}
            onChange={event => setSelectedCountry(event.target.value)}
          >
            <option>All countries</option>
            {countries.map(country => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>

          <select
            value={selectedSource}
            onChange={event => setSelectedSource(event.target.value)}
          >
            <option>All sources</option>
            {sources.map(source => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>

          <select
            value={sortOrder}
            onChange={event => setSortOrder(event.target.value)}
            aria-label="Sort articles"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
          </select>

          {filtersActive && (
            <button
              className="news-reset"
              onClick={resetFilters}
            >
              <RotateCcw size={13} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="empty-state">
          <p>Retrieving intelligence feed...</p>
        </div>
      )}

      {/* ERROR STATE */}
      {error && (
        <div className="empty-state">
          <h3>Unable to load news</h3>
          <p>{error}</p>
          <p>Check that the FastAPI backend is running.</p>
        </div>
      )}

      {/* NO RESULTS STATE */}
      {!loading && !error && filteredArticles.length === 0 && (
        <div className="empty-state">
          <h3>No matching articles</h3>
          <p>Try changing your search or filters.</p>

          {filtersActive && (
            <button
              className="news-reset"
              onClick={resetFilters}
            >
              <RotateCcw size={13} />
              Reset filters
            </button>
          )}
        </div>
      )}

      {/* NEWS ARTICLES */}
      {!loading && !error && filteredArticles.length > 0 && (
        <>
          <div className="news-list">
            {paginatedArticles.map(article => (
              <article className="news-card" key={article.id}>
                <div className="news-card-top">
                  <span className="news-source">
                    <Newspaper size={14} />
                    {article.source}
                  </span>

                  <span className="news-date">
                  {article.published
    ? new Date(article.published).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      }).toUpperCase()
    : 'DATE UNAVAILABLE'} 
                  </span>
                </div>

                <h3>{article.title}</h3>

                <div className="news-tags">
                  {(article.countries || 'Unknown')
                    .split(',')
                    .map(country => (
                      <span className="news-tag" key={country}>
                        {country.trim()}
                      </span>
                    ))}

                  {(article.topics || '')
                    .split(',')
                    .filter(Boolean)
                    .map(topic => (
                      <span
                        className="news-tag topic-tag"
                        key={topic}
                      >
                        {topic.trim()}
                      </span>
                    ))}
                </div>

                <a
                  className="news-read-link"
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  READ ORIGINAL REPORT
                  <ExternalLink size={14} />
                </a>
              </article>
            ))}
          </div>

          {/* PAGINATION NAVIGATION */}
          {totalPages > 1 && (
            <div className="news-pagination">
              <button
                className="pagination-button"
                onClick={goToPreviousPage}
                disabled={currentPage === 1}
              >
                <ChevronLeft size={16} />
                Previous
              </button>

              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>

              <button
                className="pagination-button"
                onClick={goToNextPage}
                disabled={currentPage === totalPages}
              >
                Next
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default WorldNews
