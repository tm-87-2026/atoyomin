import { createWebhook } from './webhook.ts'

Deno.serve(createWebhook({
  channelSecret: Deno.env.get('LINE_CHANNEL_SECRET'),
  channelAccessToken: Deno.env.get('LINE_CHANNEL_ACCESS_TOKEN'),
}))
