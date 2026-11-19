import { probeWebhook } from './checkWebhook.ts'
import { createWebhook } from '../../supabase/functions/line-webhook/webhook.ts'

Deno.test('probe uses signed/incorrect/absent signature without Supabase authentication and exposes only statuses', async () => {
  let count = 0
  const handler = createWebhook({
    channelSecret: 'fictional-secret',
    channelAccessToken: 'fictional-token',
  }, () => {
    throw new Error('Unexpected reply')
  })
  const statuses = await probeWebhook(
    'https://fictional.supabase.co/functions/v1/line-webhook',
    'fictional-secret',
    (url, init) => {
      count++
      if (new Headers(init?.headers).has('authorization')) {
        throw new Error(
          'Unexpected auth',
        )
      }
      return handler(new Request(url, init))
    },
  )
  if (statuses.join(',') !== '200,401,401' || count !== 3) {
    throw new Error('Unexpected probe results')
  }
})

Deno.test('probe rejects unexpected endpoints before sending', async () => {
  for (
    const url of [
      'https://example.invalid/functions/v1/line-webhook',
      'https://fictional.supabase.co/wrong',
      'https://fictional.supabase.co/functions/v1/line-webhook?extra=1',
    ]
  ) {
    let rejected = false
    let calls = 0
    try {
      await probeWebhook(url, 'fictional-secret', () => {
        calls++
        return Promise.resolve(new Response())
      })
    } catch {
      rejected = true
    }
    if (!rejected || calls !== 0) throw new Error('Invalid URL accepted')
  }
})
