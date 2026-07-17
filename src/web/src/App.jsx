import { useState, useEffect } from 'react'

const API_BASE = ''  // Uses Vite proxy to http://localhost:8000

// Metadata chip colors by field
function MetaChip({ type, value }) {
  const classMap = {
    partner: 'chip chip-partner',
    client: 'chip chip-client',
    product: 'chip chip-product',
    region: 'chip chip-region',
    classification: value === 'PublicDemoReference' ? 'chip chip-public' : 'chip chip-classification',
  }
  return <span className={classMap[type] || 'chip'}>{value}</span>
}

// Entitlement profile panel
function EntitlementPanel({ profile }) {
  if (!profile) return (
    <div className="card">
      <h2>Entitlements</h2>
      <p style={{ fontSize: 13, color: '#718096' }}>Select a user to see their entitlements.</p>
    </div>
  )

  return (
    <div className="card">
      <h2>Entitlements</h2>
      <p style={{ fontWeight: 700, fontSize: 14, marginBottom: 12 }}>{profile.displayName}</p>
      <div className="entitlement-section">
        <div className="label">Partner</div>
        <div className="chip-row">
          <MetaChip type="partner" value={profile.partnerId} />
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Allowed Clients</div>
        <div className="chip-row">
          {profile.allowedClients.length > 0
            ? profile.allowedClients.map(c => <MetaChip key={c} type="client" value={c} />)
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None (no restricted client access)</span>
          }
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Allowed Product Lines</div>
        <div className="chip-row">
          {profile.allowedProductLines.length > 0
            ? profile.allowedProductLines.map(p => <MetaChip key={p} type="product" value={p} />)
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None</span>
          }
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Allowed Regions</div>
        <div className="chip-row">
          {profile.allowedRegions.length > 0
            ? profile.allowedRegions.map(r => <MetaChip key={r} type="region" value={r} />)
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None</span>
          }
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Global References</div>
        <div className="chip-row">
          {profile.canReadGlobalReferences
            ? <MetaChip type="client" value="✓ PublicDemoReference access" />
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>No</span>
          }
        </div>
      </div>
    </div>
  )
}

// A single search result
function ResultItem({ result }) {
  const { citation, content, chunkId } = result
  return (
    <div className="result-item">
      <div className="result-title">
        {citation.title}
        {citation.score != null && (
          <span className="score-badge">score: {citation.score.toFixed(3)}</span>
        )}
      </div>
      <div className="result-content">{content}</div>
      <div className="result-meta">
        {citation.partnerId && <MetaChip type="partner" value={citation.partnerId} />}
        {citation.clientId && citation.clientId !== 'Global' && <MetaChip type="client" value={citation.clientId} />}
        {citation.productLine && citation.productLine !== 'Global' && <MetaChip type="product" value={citation.productLine} />}
        {citation.region && citation.region !== 'Global' && <MetaChip type="region" value={citation.region} />}
        {citation.classification && <MetaChip type="classification" value={citation.classification} />}
      </div>
      {citation.sourceFile && (
        <div className="result-file">
          📄 {citation.sourceFile}{citation.sourcePage ? ` — page ${citation.sourcePage}` : ''}
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [users, setUsers] = useState([])
  const [selectedUserId, setSelectedUserId] = useState('')
  const [userProfile, setUserProfile] = useState(null)
  const [query, setQuery] = useState('')
  const [searchMode, setSearchMode] = useState('hybrid')
  const [loading, setLoading] = useState(false)
  const [searchResult, setSearchResult] = useState(null)
  const [chatMode, setChatMode] = useState(false)
  const [error, setError] = useState(null)

  // Load demo users on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/users`)
      .then(r => r.json())
      .then(data => setUsers(data.users || []))
      .catch(() => {
        // API not available — show placeholder users for demo
        setUsers([
          { userId: 'user.alpha.north@example.com', displayName: 'User Alpha North', partnerId: 'PartnerAlpha' },
          { userId: 'user.alpha.south@example.com', displayName: 'User Alpha South', partnerId: 'PartnerAlpha' },
          { userId: 'user.beta.east@example.com', displayName: 'User Beta East', partnerId: 'PartnerBeta' },
          { userId: 'user.global.reader@example.com', displayName: 'Global Reference Reader', partnerId: 'Global' },
        ])
      })
  }, [])

  // Load user entitlements when selection changes
  useEffect(() => {
    if (!selectedUserId) {
      setUserProfile(null)
      return
    }
    fetch(`${API_BASE}/api/entitlements/${encodeURIComponent(selectedUserId)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setUserProfile(data))
      .catch(() => setUserProfile(null))
  }, [selectedUserId])

  const handleSearch = async () => {
    if (!query.trim() || !selectedUserId) return
    setLoading(true)
    setError(null)
    setSearchResult(null)

    const endpoint = chatMode ? '/api/chat' : '/api/search'
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: selectedUserId, query, searchMode, topK: 8 })
      })
      const data = await res.json()
      setSearchResult(data)
    } catch (e) {
      setError('API request failed. Is the backend running? (make api)')
    } finally {
      setLoading(false)
    }
  }

  const results = searchResult?.results || searchResult?.sources || []
  const hasUnknownUser = selectedUserId && selectedUserId.includes('unknown')

  return (
    <div className="app">
      <div className="banner">
        ⚠️ <strong>Demo Only</strong> — All users, documents, and data are entirely synthetic.
        No real customers, partners, or business data is present.
      </div>

      <h1>Azure AI Search — Entitlement Filtering Demo</h1>
      <p className="subtitle">
        Demonstrates metadata-based entitlement filtering. Users only see content they are authorized to access.
      </p>

      <div className="layout">
        {/* Left panel: user selection + entitlements */}
        <div>
          <div className="card">
            <h2>1. Select Demo User</h2>
            <label>Demo User</label>
            <select value={selectedUserId} onChange={e => setSelectedUserId(e.target.value)}>
              <option value="">— Select a user —</option>
              {users.map(u => (
                <option key={u.userId} value={u.userId}>
                  {u.displayName} ({u.partnerId})
                </option>
              ))}
              <option value="unknown@example.com">Unknown User (deny-by-default demo)</option>
            </select>
          </div>

          <EntitlementPanel profile={userProfile} />

          {/* Demo transparency: generated filter */}
          {searchResult && (
            <div className="card">
              <h2>Generated Filter</h2>
              <div className="filter-label">OData filter applied to this query:</div>
              <div className="filter-box">{searchResult.filter}</div>
              <p style={{ fontSize: 11, color: '#a0aec0', marginTop: 8 }}>
                This filter is applied to every Azure AI Search query. Unauthorized documents are never returned.
              </p>
            </div>
          )}
        </div>

        {/* Right panel: search */}
        <div>
          <div className="card">
            <h2>2. Run a Query</h2>

            <div className="mode-tabs">
              {['keyword', 'vector', 'hybrid'].map(mode => (
                <button
                  key={mode}
                  className={`mode-tab ${searchMode === mode ? 'active' : ''}`}
                  onClick={() => setSearchMode(mode)}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>

            <label>Query</label>
            <textarea
              placeholder="e.g. Summarize the implementation notes for Product Line A"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) handleSearch() }}
            />

            <div className="toggle-row">
              <input
                type="checkbox"
                id="chatMode"
                checked={chatMode}
                onChange={e => setChatMode(e.target.checked)}
              />
              <label htmlFor="chatMode" style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>
                Use /api/chat (RAG with Azure OpenAI — requires ENABLE_LLM=true)
              </label>
            </div>

            <button
              className="btn btn-primary"
              style={{ marginTop: 12 }}
              onClick={handleSearch}
              disabled={loading || !selectedUserId || !query.trim()}
            >
              {loading ? 'Searching…' : 'Search'}
            </button>
          </div>

          {/* Results */}
          {loading && (
            <div className="card">
              <div className="loading">
                <div className="spinner" />
                Executing entitlement-filtered search…
              </div>
            </div>
          )}

          {error && (
            <div className="message-box warning">{error}</div>
          )}

          {searchResult && !loading && (
            <div className="card">
              <h2>Results</h2>

              {searchResult.message && (
                <div className={`message-box ${results.length === 0 ? 'warning' : ''}`}>
                  {searchResult.message}
                </div>
              )}

              {/* RAG answer (chat mode) */}
              {searchResult.answer && (
                <>
                  <div className="filter-label" style={{ marginBottom: 6 }}>Generated Answer</div>
                  <div className="answer-box">{searchResult.answer}</div>
                  <div className="filter-label" style={{ marginBottom: 8 }}>Sources ({results.length})</div>
                </>
              )}

              {results.length > 0 && !searchResult.answer && (
                <div className="result-count">
                  {results.length} result{results.length !== 1 ? 's' : ''} returned
                  {' '}for <strong>{selectedUserId}</strong>
                </div>
              )}

              {results.length === 0 && !searchResult.message && (
                <div className="empty-state">
                  No results. Either the index is empty or your entitlements do not match any documents.
                </div>
              )}

              {results.map((r, i) => (
                <ResultItem key={r.chunkId || i} result={r} />
              ))}
            </div>
          )}

          {/* Sample queries panel */}
          {!searchResult && !loading && (
            <div className="card">
              <h2>Try These Sample Queries</h2>
              {[
                { user: 'user.alpha.north@example.com', q: 'Summarize Product Line A implementation notes' },
                { user: 'user.alpha.south@example.com', q: 'What are the operational risks?' },
                { user: 'user.beta.east@example.com', q: 'Show implementation details for ClientEast' },
                { user: 'user.alpha.north@example.com', q: 'Summarize ClientEast implementation notes' },
                { user: 'user.global.reader@example.com', q: 'What reference guidance is available?' },
              ].map((sample, i) => (
                <div key={i} style={{ marginBottom: 10 }}>
                  <button
                    style={{
                      background: 'none', border: '1px solid #e2e8f0', borderRadius: 6,
                      padding: '6px 12px', cursor: 'pointer', textAlign: 'left',
                      width: '100%', fontSize: 12, color: '#4a5568'
                    }}
                    onClick={() => {
                      setSelectedUserId(sample.user)
                      setQuery(sample.q)
                    }}
                  >
                    <span style={{ fontWeight: 700, color: '#1a3a5c' }}>{sample.user.split('@')[0]}</span>
                    <br />"{sample.q}"
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
