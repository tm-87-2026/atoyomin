// 秘密は標準入力だけで受け取り、応答本文や例外の詳細は出力しない。
export async function probeWebhook(
  url: string,
  secret: string,
  fetcher: typeof fetch = fetch,
) {
  const target = new URL(url)
  const remote = target.protocol === 'https:' &&
    /^[a-z0-9-]+\.supabase\.co$/.test(target.hostname)
  const local = target.protocol === 'http:' &&
    target.hostname === '127.0.0.1' && target.port === '54321'
  if (
    (!remote && !local) || target.pathname !== '/functions/v1/line-webhook' ||
    target.search || target.hash || target.username || target.password ||
    !secret
  ) throw new Error('invalid_probe_configuration')
  const body = '{"events":[]}'
  const encoder = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const bytes = new Uint8Array(
    await crypto.subtle.sign('HMAC', key, encoder.encode(body)),
  )
  const valid = btoa(String.fromCharCode(...bytes))
  bytes[0] ^= 1
  const invalid = btoa(String.fromCharCode(...bytes))
  const statuses: number[] = []
  for (const signature of [valid, invalid, undefined]) {
    const response = await fetcher(target, {
      method: 'POST',
      body,
      headers: signature ? { 'x-line-signature': signature } : {},
      redirect: 'error',
      signal: AbortSignal.timeout(10000),
    })
    statuses.push(response.status)
    await response.body?.cancel()
  }
  return statuses
}

if (import.meta.main) {
  try {
    const secret = await new Response(Deno.stdin.readable).text()
    const statuses = await probeWebhook(Deno.args[0], secret)
    for (const status of statuses) console.log(status)
    if (statuses.join(',') !== '200,401,401') Deno.exitCode = 1
  } catch {
    console.error('probe_failed')
    Deno.exitCode = 1
  }
}
