import React from 'react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDiagnostics: false,
    }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('UrbanMind Runtime Error caught by ErrorBoundary:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    if (this.props.onReset) {
      this.props.onReset()
    } else {
      window.location.reload()
    }
  }

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, showDiagnostics } = this.state
      const errorMessage = error?.message || 'An unexpected rendering error occurred.'

      return (
        <div className="app-shell" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
          <div className="panel-card" style={{ maxWidth: '640px', width: '100%', padding: '2rem', border: '1px solid rgba(239, 68, 68, 0.3)', background: 'rgba(15, 23, 42, 0.95)', backdropFilter: 'blur(16px)', boxShadow: '0 20px 40px rgba(0,0,0,0.5)', borderRadius: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ef4444', fontSize: '1.25rem', fontWeight: 'bold' }}>
                ⚠️
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.25rem', color: '#f8fafc' }}>Interface Recovery</h2>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>UrbanMind protected against a component rendering failure</span>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              The application encountered an unexpected data format or state transition. The system has prevented a blank screen and preserved application diagnostics.
            </p>

            <div style={{ background: 'rgba(0, 0, 0, 0.35)', padding: '0.85rem 1rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.08)', marginBottom: '1.25rem', fontFamily: 'var(--font-mono, monospace)', fontSize: '0.82rem', color: '#f87171', wordBreak: 'break-word' }}>
              <strong>Error:</strong> {errorMessage}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <button
                type="button"
                className="accent"
                onClick={this.handleReset}
                style={{ padding: '0.55rem 1.25rem' }}
              >
                🔄 Reset & Reload
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={() => this.setState(prev => ({ showDiagnostics: !prev.showDiagnostics }))}
                style={{ padding: '0.55rem 1rem', fontSize: '0.82rem' }}
              >
                {showDiagnostics ? 'Hide Technical Diagnostics' : 'View Technical Diagnostics'}
              </button>
            </div>

            {showDiagnostics && (
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(0, 0, 0, 0.45)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '0.75rem', color: '#cbd5e1', maxHeight: '220px', overflowY: 'auto', fontFamily: 'var(--font-mono, monospace)' }}>
                <div style={{ fontWeight: 600, color: '#38bdf8', marginBottom: '0.4rem' }}>Component Stack Trace:</div>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                  {errorInfo?.componentStack || error?.stack || 'No stack trace available.'}
                </pre>
              </div>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
