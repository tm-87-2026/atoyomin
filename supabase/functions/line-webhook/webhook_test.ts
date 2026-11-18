import { createWebhook } from './webhook.ts'

const config = {
  channelSecret: 'fictional-secret',
  channelAccessToken: 'fictional-token',
}
const encoder = new TextEncoder()
function equal(actual: unknown, expected: unknown) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(
      `Expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`,
    )
  }
}
async function signed(body: string, secret = config.channelSecret) {
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  return btoa(
    String.fromCharCode(
      ...new Uint8Array(
        await crypto.subtle.sign('HMAC', key, encoder.encode(body)),
      ),
    ),
  )
}
async function request(body: string, signature?: string) {
  return new Request('https://example.invalid', {
    method: 'POST',
    body,
    headers: { 'x-line-signature': signature ?? await signed(body) },
  })
}
const textEvent = {
  type: 'message',
  source: { type: 'user', userId: 'fictional-user' },
  message: { type: 'text', text: '架空本文\n日本語' },
  replyToken: 'fictional-reply',
}

Deno.test('signature rejection never calls the reply API, including invalid JSON before authentication', async () => {
  let calls = 0
  const handler = createWebhook(config, () => {
    calls++
    return Promise.resolve(new Response())
  })
  const body = JSON.stringify({ events: [textEvent] })
  for (
    const signature of [
      '',
      '%%%invalid',
      await signed(body, 'wrong-key'),
      await signed(body + '\n'),
      'YQ==',
    ]
  ) {
    equal((await handler(await request(body, signature))).status, 401)
  }
  equal((await handler(await request('not json', 'bad'))).status, 401)
  equal(
    (await handler(
      new Request('https://example.invalid', { method: 'POST', body }),
    )).status,
    401,
  )
  equal(calls, 0)
})

Deno.test('method, missing config, empty events and invalid authenticated envelopes', async () => {
  let calls = 0
  const fetcher = () => {
    calls++
    return Promise.resolve(new Response())
  }
  const handler = createWebhook(config, fetcher)
  equal((await handler(new Request('https://example.invalid'))).status, 405)
  for (
    const missing of [{}, { channelSecret: 'x' }, { channelAccessToken: 'x' }]
  ) {
    equal(
      (await createWebhook(missing, fetcher)(await request('{}'))).status,
      500,
    )
  }
  equal((await handler(await request('{\n"events": []\n}'))).status, 200)
  for (const body of ['{', 'null', '[]', '{}', '{"events": null}']) {
    equal((await handler(await request(body))).status, 400)
  }
  equal(calls, 0)
})

Deno.test('only one-to-one text events reply with the fixed confirmation, preserving raw Japanese/newline bytes', async () => {
  const calls: { url: string; init: RequestInit | undefined }[] = []
  const handler = createWebhook(config, (url, init) => {
    calls.push({ url: String(url), init })
    return Promise.resolve(new Response())
  })
  const ignored = [
    null,
    {},
    { ...textEvent, type: 'follow' },
    { ...textEvent, source: { type: 'group' } },
    { ...textEvent, source: { type: 'room' } },
    { ...textEvent, message: { type: 'image' } },
    { ...textEvent, message: { type: 'text', text: 1 } },
    { ...textEvent, replyToken: '' },
    { ...textEvent, replyToken: null },
  ]
  const response = await handler(
    await request(
      JSON.stringify(
        {
          events: [...ignored, textEvent, {
            ...textEvent,
            replyToken: 'fictional-second',
          }],
        },
        null,
        2,
      ),
    ),
  )
  equal(response.status, 200)
  equal(calls.length, 2)
  equal(calls[0].url, 'https://api.line.me/v2/bot/message/reply')
  equal(calls[0].init?.method, 'POST')
  equal(
    new Headers(calls[0].init?.headers).get('authorization'),
    'Bearer fictional-token',
  )
  equal(
    new Headers(calls[0].init?.headers).get('content-type'),
    'application/json',
  )
  equal(JSON.parse(String(calls[0].init?.body)), {
    replyToken: 'fictional-reply',
    messages: [{
      type: 'text',
      text:
        'メッセージを受信しました。接続確認用の返信です。記事は保存していません。',
    }],
  })
  equal(JSON.parse(String(calls[1].init?.body)).replyToken, 'fictional-second')
  equal(await response.text(), 'ok')
})

Deno.test('reply failures return 502, process every event once and never expose upstream data', async () => {
  for (const fail of ['http', 'exception']) {
    let calls = 0
    const logs: unknown[][] = []
    const original = console.error
    console.error = (...args: unknown[]) => {
      logs.push(args)
    }
    try {
      const handler = createWebhook(config, () => {
        calls++
        if (calls === 2) return Promise.resolve(new Response())
        if (fail === 'exception') {
          return Promise.reject(
            new Error('fictional-secret fictional-user 架空本文'),
          )
        }
        return Promise.resolve(
          new Response('fictional-secret fictional-user 架空本文', {
            status: 429,
          }),
        )
      })
      const response = await handler(
        await request(JSON.stringify({ events: [textEvent, textEvent] })),
      )
      equal(response.status, 502)
      equal(calls, 2)
      equal(await response.text(), 'reply_failed')
      equal(
        logs,
        fail === 'http' ? [['reply_failed', 429]] : [['reply_failed']],
      )
    } finally {
      console.error = original
    }
  }
})

Deno.test('reply is aborted after five seconds without retry', async () => {
  let calls = 0
  let aborted = false
  const started = performance.now()
  const handler = createWebhook(config, (_url, init) => {
    calls++
    return new Promise<Response>((resolve, reject) => {
      // 未実装でもテストが終了できるよう、上限を設ける。
      const guard = setTimeout(() => resolve(new Response()), 5500)
      init?.signal?.addEventListener('abort', () => {
        clearTimeout(guard)
        aborted = true
        reject(new Error('fictional-upstream-detail'))
      }, { once: true })
    })
  })
  const response = await handler(
    await request(JSON.stringify({ events: [textEvent] })),
  )
  equal(response.status, 502)
  equal(aborted, true)
  equal(calls, 1)
  if (performance.now() - started < 4900) {
    throw new Error('Aborted before the configured timeout')
  }
})
