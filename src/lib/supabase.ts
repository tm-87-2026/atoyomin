import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

export const supabaseConfigurationError =
  supabaseUrl === undefined || supabasePublishableKey === undefined
    ? 'VITE_SUPABASE_URLとVITE_SUPABASE_PUBLISHABLE_KEYを設定してください。'
    : undefined

export const supabase =
  supabaseConfigurationError === undefined
    ? createClient<Database>(supabaseUrl, supabasePublishableKey)
    : undefined
