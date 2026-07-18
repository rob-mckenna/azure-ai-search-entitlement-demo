import { useState, useEffect } from 'react'

const API_BASE = ''

const SAMPLE_QUERIES = [
  { user: 'user.alpha.north@example.com', q: 'Summarize Product Line A implementation notes' },
  { user: 'user.alpha.south@example.com', q: 'What are the operational risks?' },
  { user: 'user.beta.east@example.com', q: 'Show implementation details for ClientEast' },
  { user: 'user.alpha.north@example.com', q: 'Summarize ClientEast implementation notes' },
  { user: 'user.global.reader@example.com', q: 'What reference guidance is available?' },
]

function createPaneState() {
  return {
    selectedUserId: '',
    userProfile: null,
    query: '',
    searchMode: 'hybrid',
    loading: false,
    searchResult: null,
    chatMode: false,
    error: null,
  }
}

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

function EntitlementPanel({ profile }) {
  if (!profile) {
    return (
      <div className="card">
        <h2>Entitlements</h2>
        <p style={{ fontSize: 13, color: '#718096' }}>Select a user to see their entitlements.</p>
      </div>
    )
  }

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
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None (no restricted client access)</span>}
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Allowed Product Lines</div>
        <div className="chip-row">
          {profile.allowedProductLines.length > 0
            ? profile.allowedProductLines.map(p => <MetaChip key={p} type="product" value={p} />)
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None</span>}
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Allowed Regions</div>
        <div className="chip-row">
          {profile.allowedRegions.length > 0
            ? profile.allowedRegions.map(r => <MetaChip key={r} type="region" value={r} />)
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>None</span>}
        </div>
      </div>
      <div className="entitlement-section">
        <div className="label">Global References</div>
        <div className="chip-row">
          {profile.canReadGlobalReferences
            ? <MetaChip type="client" value="✓ PublicDemoReference access" />
            : <span style={{ fontSize: 12, color: '#a0aec0' }}>No</span>}
        </div>
      </div>
    </div>
  )
}

function ResultItem({ result }) {
  const { citation, content } = result
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
  const [compareMode, setCompareMode] = useState(false)
  const [panes, setPanes] = useState({
    left: createPaneState(),
    right: createPaneState(),
  })

  useEffect(() => {
    fetch(`${API_BASE}/api/users`)
      .then(r => r.json())
      .then(data => setUsers(data.users || []))
      .catch(() => {
        setUsers([
          { userId: 'user.alpha.north@example.com', displayName: 'User Alpha North', partnerId: 'PartnerAlpha' },
          { userId: 'user.alpha.south@example.com', displayName: 'User Alpha South', partnerId: 'PartnerAlpha' },
          { userId: 'user.beta.east@example.com', displayName: 'User Beta East', partnerId: 'PartnerBeta' },
          { userId: 'user.global.reader@example.com', displayName: 'Global Reference Reader', partnerId: 'Global' },
        ])
      })
  }, [])

  const updatePane = (paneKey, patch) => {
    setPanes(prev => ({
      ...prev,
      [paneKey]: {
        ...prev[paneKey],
        ...patch,
      },
    }))
  }

  const updatePaneWithCallback = (paneKey, callback) => {
    setPanes(prev => ({
      ...prev,
      [paneKey]: callback(prev[paneKey]),
    }))
  }

  const loadEntitlements = async (paneKey, userId) => {
    updatePaneWithCallback(paneKey, pane => ({
      ...pane,
      selectedUserId: userId,
      userProfile: null,
    }))

    if (!userId) return

    try {
      const response = await fetch(`${API_BASE}/api/entitlements/${encodeURIComponent(userId)}`)
      const data = response.ok ? await response.json() : null
      setPanes(prev => {
        if (prev[paneKey].selectedUserId !== userId) return prev
        return {
          ...prev,
          [paneKey]: {
            ...prev[paneKey],
            userProfile: data,
          },
        }
      })
    } catch {
      setPanes(prev => {
        if (prev[paneKey].selectedUserId !== userId) return prev
        return {
          ...prev,
          [paneKey]: {
            ...prev[paneKey],
            userProfile: null,
          },
        }
      })
    }
  }

  const runSearch = async paneKey => {
    const pane = panes[paneKey]
    if (!pane.query.trim() || !pane.selectedUserId) return

    updatePane(paneKey, { loading: true, error: null, searchResult: null })
    const endpoint = pane.chatMode ? '/api/chat' : '/api/search'

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: pane.selectedUserId,
          query: pane.query,
          searchMode: pane.searchMode,
          topK: 8,
        }),
      })
      const data = await res.json()
      updatePane(paneKey, { searchResult: data })
    } catch {
      updatePane(paneKey, { error: 'API request failed. Is the backend running? (make api)' })
    } finally {
      updatePane(paneKey, { loading: false })
    }
  }

  const applySingleSample = sample => {
    updatePane('left', {
      selectedUserId: sample.user,
      query: sample.q,
      searchResult: null,
      error: null,
      loading: false,
    })
    loadEntitlements('left', sample.user)
  }

  const applyCompareSample = (targetPane, queryText) => {
    if (targetPane === 'both') {
      updatePane('left', { query: queryText })
      updatePane('right', { query: queryText })
      return
    }
    updatePane(targetPane, { query: queryText })
  }

  const renderUserAndEntitlement = (paneKey, pane, headingPrefix) => (
    <>
      <div className="card">
        <h2>{headingPrefix}. Select Demo User</h2>
        <label>Demo User</label>
        <select value={pane.selectedUserId} onChange={e => loadEntitlements(paneKey, e.target.value)}>
          <option value="">— Select a user —</option>
          {users.map(u => (
            <option key={u.userId} value={u.userId}>
              {u.displayName} ({u.partnerId})
            </option>
          ))}
          <option value="unknown@example.com">Unknown User (deny-by-default demo)</option>
        </select>
      </div>

      <EntitlementPanel profile={pane.userProfile} />

      {pane.searchResult && (
        <div className="card">
          <h2>Generated Filter</h2>
          <div className="filter-label">OData filter applied to this query:</div>
          <div className="filter-box">{pane.searchResult.filter}</div>
          <p style={{ fontSize: 11, color: '#a0aec0', marginTop: 8 }}>
            This filter is applied to every Azure AI Search query. Unauthorized documents are never returned.
          </p>
        </div>
      )}
    </>
  )

  const renderQueryAndResults = (paneKey, pane, headingPrefix) => {
    const results = pane.searchResult?.results || pane.searchResult?.sources || []

    return (
      <>
        <div className="card">
          <h2>{headingPrefix}. Run a Query</h2>

          <div className="mode-tabs">
            {['keyword', 'vector', 'hybrid'].map(mode => (
              <button
                key={`${paneKey}-${mode}`}
                className={`mode-tab ${pane.searchMode === mode ? 'active' : ''}`}
                onClick={() => updatePane(paneKey, { searchMode: mode })}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>

          <label>Query</label>
          <textarea
            placeholder="e.g. Summarize the implementation notes for Product Line A"
            value={pane.query}
            onChange={e => updatePane(paneKey, { query: e.target.value })}
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) runSearch(paneKey) }}
          />

          <div className="toggle-row">
            <input
              type="checkbox"
              id={`chatMode-${paneKey}`}
              checked={pane.chatMode}
              onChange={e => updatePane(paneKey, { chatMode: e.target.checked })}
            />
            <label htmlFor={`chatMode-${paneKey}`} style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>
              Use /api/chat (RAG with Azure OpenAI — requires ENABLE_LLM=true)
            </label>
          </div>

          <button
            className="btn btn-primary"
            style={{ marginTop: 12 }}
            onClick={() => runSearch(paneKey)}
            disabled={pane.loading || !pane.selectedUserId || !pane.query.trim()}
          >
            {pane.loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {pane.loading && (
          <div className="card">
            <div className="loading">
              <div className="spinner" />
              Executing entitlement-filtered search…
            </div>
          </div>
        )}

        {pane.error && (
          <div className="message-box warning">{pane.error}</div>
        )}

        {pane.searchResult && !pane.loading && (
          <div className="card">
            <h2>Results</h2>

            {pane.searchResult.message && (
              <div className={`message-box ${results.length === 0 ? 'warning' : ''}`}>
                {pane.searchResult.message}
              </div>
            )}

            {pane.searchResult.answer && (
              <>
                <div className="filter-label" style={{ marginBottom: 6 }}>Generated Answer</div>
                <div className="answer-box">{pane.searchResult.answer}</div>
                <div className="filter-label" style={{ marginBottom: 8 }}>Sources ({results.length})</div>
              </>
            )}

            {results.length > 0 && !pane.searchResult.answer && (
              <div className="result-count">
                {results.length} result{results.length !== 1 ? 's' : ''} returned for <strong>{pane.selectedUserId}</strong>
              </div>
            )}

            {results.length === 0 && !pane.searchResult.message && (
              <div className="empty-state">
                No results. Either the index is empty or your entitlements do not match any documents.
              </div>
            )}

            {results.map((result, i) => (
              <ResultItem key={result.chunkId || `${paneKey}-${i}`} result={result} />
            ))}
          </div>
        )}
      </>
    )
  }

  const leftPane = panes.left
  const rightPane = panes.right

  return (
    <div className={`app ${compareMode ? 'compare-mode-on' : ''}`}>
      <div className="banner">
        ⚠️ <strong>Demo Only</strong> — All users, documents, and data are entirely synthetic.
        No real customers, partners, or business data is present.
      </div>

      <h1>Azure AI Search — Entitlement Filtering Demo</h1>
      <p className="subtitle">
        Demonstrates metadata-based entitlement filtering. Users only see content they are authorized to access.
      </p>

      <div className="card compare-mode-toggle">
        <div className="toggle-row">
          <input
            type="checkbox"
            id="compareMode"
            checked={compareMode}
            onChange={e => setCompareMode(e.target.checked)}
          />
          <label htmlFor="compareMode" style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 600 }}>
            Enable compare mode (left/right users)
          </label>
        </div>
      </div>

      {!compareMode && (
        <div className="layout">
          <div>
            {renderUserAndEntitlement('left', leftPane, '1')}
          </div>
          <div>
            {renderQueryAndResults('left', leftPane, '2')}
            {!leftPane.searchResult && !leftPane.loading && (
              <div className="card">
                <h2>Try These Sample Queries</h2>
                {SAMPLE_QUERIES.map((sample, i) => (
                  <div key={i} style={{ marginBottom: 10 }}>
                    <button
                      className="sample-button"
                      onClick={() => applySingleSample(sample)}
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
      )}

      {compareMode && (
        <>
          <div className="compare-layout">
            <div className="compare-pane">
              <div className="compare-pane-title">Left Pane</div>
              {renderUserAndEntitlement('left', leftPane, '1')}
              {renderQueryAndResults('left', leftPane, '2')}
            </div>
            <div className="compare-pane">
              <div className="compare-pane-title">Right Pane</div>
              {renderUserAndEntitlement('right', rightPane, '1')}
              {renderQueryAndResults('right', rightPane, '2')}
            </div>
          </div>

          <div className="card">
            <h2>Sample Queries for Compare Mode</h2>
            <p className="sample-query-helper">
              Apply sample text to either side (or both), then run each query independently.
            </p>
            <div className="sample-query-grid">
              {SAMPLE_QUERIES.map((sample, i) => (
                <div key={i} className="sample-query-row">
                  <div className="sample-query-text">
                    <strong>{sample.user.split('@')[0]}</strong> — "{sample.q}"
                  </div>
                  <div className="sample-query-actions">
                    <button className="btn btn-secondary" onClick={() => applyCompareSample('left', sample.q)}>Apply to Left</button>
                    <button className="btn btn-secondary" onClick={() => applyCompareSample('right', sample.q)}>Apply to Right</button>
                    <button className="btn btn-secondary" onClick={() => applyCompareSample('both', sample.q)}>Apply to Both</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
