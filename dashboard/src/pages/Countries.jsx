
import { useEffect, useMemo, useState } from "react";
import { Search, Globe2, ArrowUpRight, RotateCcw } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";


function formatDate(dateString) {
  if (!dateString) return "Date unavailable";

  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}


function Countries() {
  const [countries, setCountries] = useState([]);
  const [overview, setOverview] = useState(null);

  const [selectedCountry, setSelectedCountry] = useState("");
  const [countryDetails, setCountryDetails] = useState(null);

  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState("articles");

  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");


  // Load the country directory
  useEffect(() => {
    async function loadCountries() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_BASE}/api/countries`);

        if (!response.ok) {
          throw new Error("Unable to retrieve country data.");
        }

        const data = await response.json();

        setCountries(data.countries || []);
        setOverview(data);

        if (data.countries?.length > 0) {
          setSelectedCountry(data.countries[0].country);
        }

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadCountries();
  }, []);


  // Load details whenever a country is selected
  useEffect(() => {
    if (!selectedCountry) return;

    async function loadCountryDetails() {
      try {
        setDetailLoading(true);
        setDetailError("");
        setCountryDetails(null);

        const response = await fetch(
          `${API_BASE}/api/countries/${encodeURIComponent(selectedCountry)}`
        );

        if (!response.ok) {
          throw new Error("Unable to retrieve this country's articles.");
        }

        const data = await response.json();
        setCountryDetails(data);

      } catch (err) {
        setDetailError(err.message);
      } finally {
        setDetailLoading(false);
      }
    }

    loadCountryDetails();
  }, [selectedCountry]);


  // Search and sort the country directory
  const filteredCountries = useMemo(() => {
    const filtered = countries.filter((item) =>
      item.country.toLowerCase().includes(search.toLowerCase())
    );

    return [...filtered].sort((a, b) => {
      if (sortOrder === "alphabetical") {
        return a.country.localeCompare(b.country);
      }

      return b.article_count - a.article_count;
    });
  }, [countries, search, sortOrder]);


  const timeline = countryDetails?.coverage_timeline || [];
  const maxDailyCoverage = Math.max(
    1,
    ...timeline.map((item) => item.article_count)
  );


  function resetSearch() {
    setSearch("");
    setSortOrder("articles");
  }


  return (
    <section className="page-section countries-page">

      {/* Page introduction */}
      <span className="section-kicker">GEOGRAPHIC INTELLIGENCE</span>

      <h1>Regions & Countries</h1>

      <p>
        Explore country-level news coverage, political developments and
        international affairs through the STATECRAFT MONITOR database.
      </p>


      {/* Loading and error states */}
      {loading && (
        <div className="country-status">
          Loading country intelligence...
        </div>
      )}

      {!loading && error && (
        <div className="country-status country-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            <RotateCcw size={14} /> Reload page
          </button>
        </div>
      )}


      {!loading && !error && overview && (
        <>

          {/* Database overview */}
          <div className="country-overview">

            <div className="country-stat">
              <span className="country-stat-label">COUNTRIES IDENTIFIED</span>
              <strong>{overview.country_count}</strong>
              <small>Across the current database</small>
            </div>

            <div className="country-stat">
              <span className="country-stat-label">ARTICLES WITH COUNTRY DATA</span>
              <strong>{overview.articles_with_countries}</strong>
              <small>Articles with detected countries</small>
            </div>

          </div>


          {/* Country directory and detail panel */}
          <div className="country-workspace">

            <div className="country-directory">

              <div className="country-directory-heading">
                <div>
                  <span className="section-kicker">COUNTRY INDEX</span>
                  <h2>Country Directory</h2>
                </div>

                <Globe2 size={21} />
              </div>


              {/* Search */}
              <div className="news-search country-search">
                <Search size={17} />

                <input
                  type="text"
                  placeholder="Search countries..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>


              {/* Sorting */}
              <div className="country-directory-controls">
                <span>{filteredCountries.length} countries</span>

                <select
                  value={sortOrder}
                  onChange={(event) => setSortOrder(event.target.value)}
                >
                  <option value="articles">Most articles</option>
                  <option value="alphabetical">A to Z</option>
                </select>
              </div>


              {/* Country list */}
              <div className="country-list">

                {filteredCountries.map((item) => (
                  <button
                    key={item.country}
                    className={`country-list-item ${
                      selectedCountry === item.country ? "selected" : ""
                    }`}
                    onClick={() => setSelectedCountry(item.country)}
                    aria-pressed={selectedCountry === item.country}
                  >
                    <span className="country-list-name">
                      {item.country}
                    </span>

                    <span className="country-list-count">
                      {item.article_count}
                      <ArrowUpRight size={13} />
                    </span>
                  </button>
                ))}

                {filteredCountries.length === 0 && (
                  <div className="country-empty">
                    No matching countries found.
                  </div>
                )}

              </div>

              <button className="country-reset" onClick={resetSearch}>
                <RotateCcw size={13} />
                Reset directory
              </button>

            </div>


            {/* Selected country details */}
            <div className="country-detail">

              {detailLoading && (
                <div className="country-status">
                  Loading country profile...
                </div>
              )}

              {!detailLoading && detailError && (
                <div className="country-status country-error">
                  {detailError}
                </div>
              )}

              {!detailLoading && countryDetails && (
                <>

                  <div className="country-detail-header">
                    <span className="section-kicker">
                      COUNTRY INTELLIGENCE PROFILE
                    </span>

                    <h2>{countryDetails.country}</h2>

                    <p>
                      News coverage and recorded developments associated
                      with this country in the current database.
                    </p>
                  </div>


                  {/* Selected country coverage metrics */}
                  <div className="country-profile-stats">
                    <div className="country-profile-stat">
                      <span>ARTICLES COVERED</span>
                      <strong>{countryDetails.article_count}</strong>
                    </div>

                    <div className="country-profile-stat">
                      <span>NEWS SOURCES</span>
                      <strong>{countryDetails.source_count}</strong>
                    </div>

                    <div className="country-profile-stat">
                      <span>TOPICS COVERED</span>
                      <strong>{countryDetails.topic_count}</strong>
                    </div>

                    <div className="country-profile-stat">
                      <span>LATEST COVERAGE</span>
                      <strong className="country-profile-date">
                        {formatDate(countryDetails.latest_coverage)}
                      </strong>
                    </div>
                  </div>


                  {/* Daily country coverage timeline */}
                  <div className="country-timeline">
                    <div className="country-timeline-heading">
                      <div>
                        <span className="section-kicker">MEDIA ATTENTION OVER TIME</span>
                        <h3>Coverage Timeline</h3>
                      </div>
                      <span>{timeline.length} publication dates</span>
                    </div>

                    {timeline.length > 0 ? (
                      <div
                        className="country-timeline-chart"
                        role="img"
                        aria-label={`Daily article coverage for ${countryDetails.country}`}
                      >
                        {timeline.map((item) => (
                          <div className="country-timeline-column" key={item.date}>
                            <span className="country-timeline-value">
                              {item.article_count}
                            </span>
                            <div className="country-timeline-bar-track">
                              <div
                                className="country-timeline-bar"
                                style={{
                                  height: `${(item.article_count / maxDailyCoverage) * 100}%`,
                                }}
                              />
                            </div>
                            <time>{formatDate(item.date).replace(/\\s\\d{4}$/, "")}</time>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="country-muted">
                        No publication dates are available for this country.
                      </p>
                    )}
                  </div>


                  {/* Topic breakdown */}
                  <div className="country-breakdown">

                    <div className="country-breakdown-panel">
                      <h3>Topic Distribution</h3>

                      {countryDetails.topics.length > 0 ? (
                        countryDetails.topics.map((item) => (
                          <div className="country-breakdown-row" key={item.topic}>
                            <span>{item.topic}</span>
                            <strong>{item.article_count}</strong>
                          </div>
                        ))
                      ) : (
                        <p className="country-muted">No topic data available.</p>
                      )}
                    </div>


                    {/* Source breakdown */}
                    <div className="country-breakdown-panel">
                      <h3>News Sources</h3>

                      {countryDetails.sources.length > 0 ? (
                        countryDetails.sources.map((item) => (
                          <div className="country-breakdown-row" key={item.source}>
                            <span>{item.source}</span>
                            <strong>{item.article_count}</strong>
                          </div>
                        ))
                      ) : (
                        <p className="country-muted">No source data available.</p>
                      )}
                    </div>

                  </div>


                  {/* Country-specific headlines */}
                  <div className="country-articles-heading">
                    <div>
                      <span className="section-kicker">LATEST COVERAGE</span>
                      <h3>Related Headlines</h3>
                    </div>

                    <span>{countryDetails.articles.length} articles</span>
                  </div>


                  <div className="country-article-list">

                    {countryDetails.articles.map((article) => (
                      <article className="country-article" key={article.id}>

                        <div className="country-article-meta">
                          <span>{article.source}</span>
                          <time>{formatDate(article.published)}</time>
                        </div>

                        <h4>{article.title}</h4>

                        <div className="news-tags">
                          {article.topics &&
                            article.topics.split(",").map((topic) => (
                              <span
                                className="news-tag topic-tag"
                                key={topic.trim()}
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
                          <ArrowUpRight size={13} />
                        </a>

                      </article>
                    ))}

                  </div>

                </>
              )}

              {!detailLoading && !countryDetails && !detailError && (
                <div className="country-status">
                  Select a country to explore its intelligence profile.
                </div>
              )}

            </div>

          </div>

          <div className="country-data-note">
            <span className="status-dot"></span>
            COUNTRY COVERAGE IS BASED ON DETECTED ENTITIES IN THE NEWS DATABASE
          </div>

        </>
      )}

    </section>
  );
}

export default Countries;
