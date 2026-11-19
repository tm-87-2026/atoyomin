export type AppStatus = {
  id: number
  message: string
  updated_at: string
}

export type Database = {
  public: {
    Tables: {
      app_status: {
        Row: AppStatus
        Insert: AppStatus
        Update: Partial<AppStatus>
        Relationships: []
      }
    }
    Views: Record<string, never>
    Functions: Record<string, never>
    Enums: Record<string, never>
    CompositeTypes: Record<string, never>
  }
}
