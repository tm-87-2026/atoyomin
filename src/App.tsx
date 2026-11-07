import { useEffect, useState } from 'react'
import type { AppStatus } from './lib/database.types'
import { supabase, supabaseConfigurationError } from './lib/supabase'

type ConnectionState =
  | { kind: 'loading' }
  | { kind: 'configured' }
  | { kind: 'connected'; status: AppStatus }
  | { kind: 'error' }

function App() {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    kind: supabaseConfigurationError === undefined ? 'loading' : 'configured',
  })

  useEffect(() => {
    const client = supabase

    if (client === undefined) {
      return
    }

    let ignoreResult = false

    const loadAppStatus = async () => {
      const { data, error } = await client
        .from('app_status')
        .select('id, message, updated_at')
        .eq('id', 1)
        .single()

      if (ignoreResult) {
        return
      }

      if (error !== null) {
        setConnectionState({ kind: 'error' })
        return
      }

      setConnectionState({ kind: 'connected', status: data })
    }

    void loadAppStatus()

    return () => {
      ignoreResult = true
    }
  }, [])

  return (
    <main>
      <section aria-labelledby="page-title" className="card">
        <p className="eyebrow">atoyomin / infrastructure check</p>
        <h1 id="page-title">あとよみん</h1>
        <p className="introduction">
          Cloudflare PagesからSupabaseへ接続する最小構成です。
        </p>
        <ConnectionResult connectionState={connectionState} />
      </section>
    </main>
  )
}

function ConnectionResult({ connectionState }: { connectionState: ConnectionState }) {
  if (connectionState.kind === 'loading') {
    return <p aria-live="polite">Supabaseへの接続を確認しています。</p>
  }

  if (connectionState.kind === 'configured') {
    return (
      <p className="notice" role="status">
        {supabaseConfigurationError}
      </p>
    )
  }

  if (connectionState.kind === 'error') {
    return (
      <p className="error" role="alert">
        Supabaseへ接続できませんでした。環境変数とマイグレーションの適用状況を確認してください。
      </p>
    )
  }

  return (
    <div className="success" role="status">
      <p>{connectionState.status.message}</p>
      <p className="timestamp">
        最終更新: {new Intl.DateTimeFormat('ja-JP', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(connectionState.status.updated_at))}
      </p>
    </div>
  )
}

export default App
