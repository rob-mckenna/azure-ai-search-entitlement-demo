import { useEffect, useMemo, useState } from 'react'

const API_BASE = '' // Uses Vite proxy to http://localhost:8000

const SAMPLE_QUERIES = [
  { user: 'user.alpha.north@example.com', q: 'Summarize Product Line A implementation notes' },
  { user: 'user.alpha.south@example.com', q: 'What are the operational risks?' },
  { user: 'user.beta.east@example.com', q: 'Show implementation details for ClientEast' },
  { user: 'user.alpha.north@example.com', q: 'Summarize ClientEast implementation notes' },
  { user: 'user.global.reader@example.com', q: 'What reference guidance is available?' },
]

const DEFAULT_USERS = [
  { userId: 'user.alpha.north@example.com', displayName: 'User Alpha North', partnerId: 'PartnerAlpha' },
  { userId: 'user.alpha.south@example.com', displayName: 'User Alpha South', partnerId: 'PartnerAlpha' },
  { userId: 'user.beta.east@example.com', displayName: 'User Beta East', partnerId: 'PartnerBeta' },
  { userId: 'user.global.reader@example.com', displayName: 'Global Reference Reader', partnerId: 'Global' },
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

function EntitlementPanel({ profile, title = 'Entitlements' }) {
  if (!profile) {
    return (
      <div className="card">
        <h2>{title}</h2>
        <p className="muted">Select a user to see their entitlements.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>{title}</h2>
      <p className="profile-name">{profile.displayName}</p>

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
            : <span className="muted">None (no restricted client access)</span>}
        </div>
      </div>

      <div className="entitlement-section">
        <div className="label">Allowed Product Lines</div>
        <div className="chip-row">
          {profile.allowedProductLines.length > 0
            ? profile.allowedProductLines.map(p => <MetaChip key={p} type="product" value={p} />)
            : <span className="muted">None</span>}
        </div>
      </div>

      <div className="entitlement-section">
        <div className="label">Allowed Regions</div>
        <div className="chip-row">
          {profile.allowedRegions.length > 0
            ? profile.allowedRegions.map(r => <MetaChip key={r} type="region" value={r} />)
            : <span className="muted">None</span>}
        </div>
      </div>

      <div className="entitlement-section">
        <div className="label">Global References</div>
        <div className="chip-row">
          {profile.canReadGlobalReferences
            ? <MetaChip type="client" value="✓ PublicDemoReference access" />
            : <span className="muted">No</span>}
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

function PaneCard({ paneKey, pane, users, onSelectUser, onQueryChange, onSearchModeChange, onChatModeChange, onSearch }) {
  const results = pane.searchResult?.results || pane.searchResult?.sources || []
  const paneTitle = paneKey === 'left' ? 'Left Pane' : 'Right Pane'

  return (
    <>
      <div className="card">
        <div className="pane-title-row">
          <h2>{paneTitle}</h2>
          <span className="pane-pill">{pane.chatMode ? 'Chat' : 'Search'}</span>
        </div>

        <label>Demo User</label>
        <select value={pane.selectedUserId} onChange={e => onSelectUser(paneKey, e.target.value)}>
          <option value="">— Select a user —</option>
          {users.map(u => (
            <option key={u.userId} value={u.userId}>
              {u.displayName} ({u.partnerId})
            </option>
          ))}
          <option value="unknown@example.com">Unknown User (deny-by-default demo)</option>
        </select>

        <div className="mode-tabs">
          {['keyword', 'vector', 'hybrid'].map(mode => (
            <button
              key={`${paneKey}-${mode}`}
              type="button"
              className={`mode-tab ${pane.searchMode === mode ? 'active' : ''}`}
              onClick={() => onSearchModeChange(paneKey, mode)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>

        <label>Query</label>
        <textarea
          placeholder="e.g. Summarize the implementation notes for Product Line A"
          value={pane.query}
          onChange={e => onQueryChange(paneKey, e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && e.ctrlKey) onSearch(paneKey)
          }}
        />

        <div className="toggle-row">
          <input
            type="checkbox"
            id={`chatMode-${paneKey}`}
            checked={pane.chatMode}
            onChange={e => onChatModeChange(paneKey, e.target.checked)}
          />
          <label htmlFor={`chatMode-${paneKey}`} className="inline-label">
            Use /api/chat (RAG with Azure OpenAI — requires ENABLE_LLM=true)
          </label>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          style={{ marginTop: 12 }}
          onClick={() => onSearch(paneKey)}
          disabled={pane.loading || !pane.selectedUserId || !pane.query.trim()}
        >
          {pane.loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      <EntitlementPanel profile={pane.userProfile} title="Entitlements" />

      {pane.searchResult && (
        <div className="card">
          <h2>Generated Filter</h2>
          <div className="filter-label">OData filter applied to this query:</div>
          <div className="filter-box">{pane.searchResult.filter}</div>
          <p className="hint">
            This filter is applied to every Azure AI Search query. Unauthorized documents are never returned.
          </p>
        </div>
      )}

      {pane.loading && (
        <div className="card">
          <div className="loading">
            <div className="spinner" />
            Executing entitlement-filtered search…
          </div>
        </div>
      )}

      {pane.error && <div className="message-box warning">{pane.error}</div>}

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

function CompareSummary({ leftPane, rightPane }) {
  const leftResults = leftPane.searchResult?.results || leftPane.searchResult?.sources || []
  const rightResults = rightPane.searchResult?.results || rightPane.searchResult?.sources || []
  const leftFilter = leftPane.searchResult?.filter || ''
  const rightFilter = rightPane.searchResult?.filter || ''

  const summary = useMemo(() => {
    if (!leftPane.searchResult && !rightPane.searchResult) return null

    return {
      sameQuery: leftPane.query.trim() === rightPane.query.trim() && !!leftPane.query.trim(),
      sameFilter: leftFilter === rightFilter && !!leftFilter,
      resultDelta: leftResults.length - rightResults.length,
    }
  }, [leftPane.query, leftPane.searchResult, leftFilter, rightPane.query, rightPane.searchResult, rightFilter, leftResults.length, rightResults.length])

  if (!summary) return null

  return (
    <div className="card">
      <h2>Compare Snapshot</h2>
      <div className="compare-summary-grid">
        <div>
          <div className="filter-label">Left user</div>
          <div className="summary-value">{leftPane.selectedUserId || 'Not selected'}</div>
        </div>
        <div>
          <div className="filter-label">Right user</div>
          <div className="summary-value">{rightPane.selectedUserId || 'Not selected'}</div>
        </div>
        <div>
          <div className="filter-label">Same query</div>
          <div className="summary-value">{summary.sameQuery ? 'Yes' : 'No'}</div>
        </div>
        <div>
          <div className="filter-label">Same filter</div>
          <div className="summary-value">{summary.sameFilter ? 'Yes' : 'No'}</div>
        </div>
        <div>
          <div className="filter-label">Left results</div>
          <div className="summary-value">{leftResults.length}</div>
        </div>
        <div>
          <div className="filter-label">Right results</div>
          <div className="summary-value">{rightResults.length}</div>
        </div>
      </div>
      <div className="compare-note">
        Result delta: {summary.resultDelta > 0 ? '+' : ''}{summary.resultDelta}
      </div>
    </div>
  )
}

function QueryHistory({ queryHistory }) {
  return (
    <div className="card">
      <h2>📋 Recent Queries</h2>
      {queryHistory.length === 0 ? (
        <p className="muted">No queries logged yet. Run a query to see it appear here.</p>
      ) : (
        <div className="history-list">
          {queryHistory.map((q, i) => (
            <div key={i} className="history-item">
              <div className="history-title">
                {q.userId.split('@')[0]} — {q.endpoint}
              </div>
              <div className="history-query">"{q.query}"</div>
              <div className="history-meta">
                {new Date(q.timestamp).toLocaleTimeString()}
                {q.searchMode ? ` • ${q.searchMode}` : ''}
              </div>
            </div>
          ))}
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
  const [queryHistory, setQueryHistory] = useState([])

  useEffect(() => {
    fetch(`${API_BASE}/api/users`)
      .then(r => r.json())
      .then(data => setUsers(data.users || []))
      .catch(() => setUsers(DEFAULT_USERS))
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_BASE}/api/query-history?limit=10`)
        .then(r => r.json())
        .then(data => setQueryHistory(data.queries || []))
        .catch(() => {})
    }, 2000)

    return () => clearInterval(interval)
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
      searchResult: null,
      error: null,
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
      setPanes(prev => {
        if (prev[paneKey].selectedUserId !== pane.selectedUserId || prev[paneKey].query !== pane.query) return prev
        return {
          ...prev,
          [paneKey]: {
            ...prev[paneKey],
            searchResult: data,
          },
        }
      })
    } catch {
      updatePane(paneKey, { error: 'API request failed. Is the backend running? (make api)' })
    } finally {
      setPanes(prev => ({
        ...prev,
        [paneKey]: {
          ...prev[paneKey],
          loading: false,
        },
      }))
    }
  }

  const applySampleQuery = sample => {
    const patch = {
      query: sample.q,
      searchResult: null,
      error: null,
      loading: false,
    }

    if (compareMode) {
      updatePane('left', patch)
      updatePane('right', patch)
      return
    }

    updatePane('left', patch)
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
          <label htmlFor="compareMode" className="inline-label strong">
            Enable compare mode (left/right users)
          </label>
        </div>
        <p className="hint">
          Compare mode is designed for same-query, different-user validation. Load each persona, then run the same query on both sides.
        </p>
      </div>

      <div className="card">
        <h2>{compareMode ? 'Sample Queries for Compare Mode' : 'Try These Sample Queries'}</h2>
        <p className="sample-query-helper">
          {compareMode
            ? 'Click a sample query to copy it into both query boxes.'
            : 'Click a sample query to populate the query box.'}
        </p>
        <div className="sample-query-grid">
          {SAMPLE_QUERIES.map((sample, i) => (
            <button
              key={i}
              type="button"
              className="sample-button"
              onClick={() => applySampleQuery(sample)}
            >
              <span className="sample-user">{sample.user.split('@')[0]}</span>
              <br />"{sample.q}"
            </button>
          ))}
        </div>
      </div>

      {!compareMode && (
        <div className="layout">
          <div>
            <PaneCard
              paneKey="left"
              pane={leftPane}
              users={users}
              onSelectUser={loadEntitlements}
              onQueryChange={(paneKey, value) => updatePane(paneKey, { query: value })}
              onSearchModeChange={(paneKey, value) => updatePane(paneKey, { searchMode: value })}
              onChatModeChange={(paneKey, value) => updatePane(paneKey, { chatMode: value })}
              onSearch={runSearch}
            />
          </div>

          <div>
            {leftPane.searchResult && (
              <div className="card">
                <h2>Search Notes</h2>
                <p className="hint">
                  Run a search to inspect the generated filter and result list. Toggle compare mode above to place two personas side by side.
                </p>
              </div>
            )}
            <QueryHistory queryHistory={queryHistory} />
          </div>
        </div>
      )}

      {compareMode && (
        <>
          <div className="compare-layout">
            <div className="compare-pane">
              <PaneCard
                paneKey="left"
                pane={leftPane}
                users={users}
                onSelectUser={loadEntitlements}
                onQueryChange={(paneKey, value) => updatePane(paneKey, { query: value })}
                onSearchModeChange={(paneKey, value) => updatePane(paneKey, { searchMode: value })}
                onChatModeChange={(paneKey, value) => updatePane(paneKey, { chatMode: value })}
                onSearch={runSearch}
              />
            </div>

            <div className="compare-pane">
              <PaneCard
                paneKey="right"
                pane={rightPane}
                users={users}
                onSelectUser={loadEntitlements}
                onQueryChange={(paneKey, value) => updatePane(paneKey, { query: value })}
                onSearchModeChange={(paneKey, value) => updatePane(paneKey, { searchMode: value })}
                onChatModeChange={(paneKey, value) => updatePane(paneKey, { chatMode: value })}
                onSearch={runSearch}
              />
            </div>
          </div>

          <CompareSummary leftPane={leftPane} rightPane={rightPane} />

          <QueryHistory queryHistory={queryHistory} />
        </>
      )}
    </div>
  )
}
