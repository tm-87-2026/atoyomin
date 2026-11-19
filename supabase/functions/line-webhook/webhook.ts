import { replyToMessage } from './reply.ts'

export interface WebhookConfig {
  channelSecret?: string
  channelAccessToken?: string
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

async function validSignature(
  body: ArrayBuffer,
  signature: string | null,
  secret: string,
) {
  if (!signature || !/^[A-Za-z0-9+/]{43}=$/.test(signature)) return false
  const decoded = Uint8Array.from(
    atob(signature),
    (character) => character.charCodeAt(0),
  )
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify'],
  )
  return crypto.subtle.verify('HMAC', key, decoded, body)
}

// 設定と通信を入口から渡し、秘密値や受信オブジェクトをログへ渡さない。
export function createWebhook(
  config: WebhookConfig,
  fetcher: typeof fetch = fetch,
) {
  return async (request: Request): Promise<Response> => {
    if (request.method !== 'POST') {
      return new Response('method_not_allowed', {
        status: 405,
        headers: { Allow: 'POST' },
      })
    }
    if (!config.channelSecret || !config.channelAccessToken) {
      return new Response('configuration_error', { status: 500 })
    }
    const accessToken = config.channelAccessToken
    const body = await request.arrayBuffer()
    if (
      !await validSignature(
        body,
        request.headers.get('x-line-signature'),
        config.channelSecret,
      )
    ) return new Response('unauthorized', { status: 401 })
    let payload: unknown
    try {
      payload = JSON.parse(new TextDecoder().decode(body))
    } catch {
      return new Response('invalid_payload', { status: 400 })
    }
    if (!isRecord(payload) || !Array.isArray(payload.events)) {
      return new Response('invalid_payload', { status: 400 })
    }
    const results = await Promise.all(
      payload.events.map((event: unknown) => {
        if (
          !isRecord(event) || event.type !== 'message' ||
          !isRecord(event.source) || event.source.type !== 'user' ||
          !isRecord(event.message) || event.message.type !== 'text' ||
          typeof event.message.text !== 'string' ||
          typeof event.replyToken !== 'string' || event.replyToken.length === 0
        ) return true
        return replyToMessage(event.replyToken, accessToken, fetcher)
      }),
    )
    return results.every(Boolean)
      ? new Response('ok')
      : new Response('reply_failed', { status: 502 })
  }
}
