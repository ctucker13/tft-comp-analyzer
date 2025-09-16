// API Types for TFT Composition Analyzer

export interface ChatRequest {
  message: string
  conversation_id?: string
  provider?: 'anthropic' | 'openai'
}

export interface ChatResponse {
  response: string
  conversation_id: string
  intent?: string
  tool_used?: string
}

export interface MLRecommendationRequest {
  gold: number
  level: number
  stage: number
  health: number
  round_number?: number
}

export interface MLRecommendationResponse {
  recommendation: string
  game_state: {
    gold: number
    level: number
    stage: number
    health: number
    game_phase: string
  }
  confidence: number
  analysis_type: string
}

export interface Champion {
  name: string
  cost: number
  traits: string[]
  type: string
}

export interface ChampionFilter {
  name?: string
  cost?: number
  trait?: string
}

export interface Composition {
  name: string
  tier: string
  win_rate: number
  avg_placement: number
  play_rate: number
  primary_trait: string
  key_champions: string[]
}

export interface TierList {
  [tier: string]: Composition[]
}

export interface MetaResponse {
  tier_lists: TierList
  raw_analysis?: string
  last_updated: string
  data_source: string
  total_compositions: number
}

export interface TrendsResponse {
  trends_analysis: string
  structured_trends: any
  parameters: {
    days_analyzed: number
    trait_filter?: string
  }
  last_updated: string
}

export interface DatabaseResponse {
  champions?: Champion[]
  total?: number
  filters_applied?: any
}

export interface HealthResponse {
  status: string
  timestamp: string
  champions: number
  traits: number
  compositions: number
  api_keys: Record<string, boolean>
}

export type TierFilter = 'S+' | 'S' | 'A' | 'B' | 'C'