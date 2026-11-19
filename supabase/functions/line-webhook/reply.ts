export async function replyToMessage(
  replyToken: string,
  accessToken: string,
  fetcher: typeof fetch,
): Promise<boolean> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 5000)
  try {
    const response = await fetcher('https://api.line.me/v2/bot/message/reply', {
      method: 'POST',
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        replyToken,
        messages: [{
          type: 'text',
          text:
            'メッセージを受信しました。接続確認用の返信です。記事は保存していません。',
        }],
      }),
    })
    await response.body?.cancel()
    if (!response.ok) console.error('reply_failed', response.status)
    return response.ok
  } catch {
    console.error('reply_failed')
    return false
  } finally {
    clearTimeout(timer)
  }
}
