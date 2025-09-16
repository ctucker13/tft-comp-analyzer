'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Trophy, Users, Clock, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'
import type { MetaResponse, TrendsResponse, Composition, TierFilter } from '@/types/api'

export default function MetaAnalysis() {
  const [tierData, setTierData] = useState<MetaResponse | null>(null)
  const [trendsData, setTrendsData] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedTier, setSelectedTier] = useState<TierFilter | 'ALL'>('ALL')
  const [expandedComps, setExpandedComps] = useState<Set<string>>(new Set())

  const tierOrder: (TierFilter | 'ALL')[] = ['ALL', 'S+', 'S', 'A', 'B', 'C']
  const tierColors = {
    'S+': 'text-red-400 bg-red-900/20 border-red-500/30',
    'S': 'text-orange-400 bg-orange-900/20 border-orange-500/30',
    'A': 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30',
    'B': 'text-green-400 bg-green-900/20 border-green-500/30',
    'C': 'text-gray-400 bg-gray-900/20 border-gray-500/30',
    'ALL': 'text-tft-gold bg-tft-gold/10 border-tft-gold/30'
  }

  useEffect(() => {
    loadTierData()
    loadTrendsData()
  }, [])

  const loadTierData = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/meta/tier-list')
      if (response.ok) {
        const data: MetaResponse = await response.json()
        setTierData(data)
      }
    } catch (error) {
      console.error('Error loading tier data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTrendsData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/meta/trends?days=7')
      if (response.ok) {
        const data: TrendsResponse = await response.json()
        setTrendsData(data)
      }
    } catch (error) {
      console.error('Error loading trends data:', error)
    }
  }

  const toggleCompExpanded = (compName: string) => {
    const newExpanded = new Set(expandedComps)
    if (newExpanded.has(compName)) {
      newExpanded.delete(compName)
    } else {
      newExpanded.add(compName)
    }
    setExpandedComps(newExpanded)
  }

  const getFilteredCompositions = (): Composition[] => {
    if (!tierData?.tier_lists) return []

    if (selectedTier === 'ALL') {
      return Object.values(tierData.tier_lists).flat()
    } else {
      return tierData.tier_lists[selectedTier] || []
    }
  }

  const formatWinRate = (rate: number) => `${(rate * 100).toFixed(1)}%`
  const formatPlayRate = (rate: number) => `${(rate * 100).toFixed(1)}%`
  const formatPlacement = (placement: number) => placement.toFixed(1)

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Meta Analysis</h2>
          <p className="text-gray-400">
            Current tier lists and trends for Set 15: K.O. Coliseum
          </p>
        </div>
        <button
          onClick={() => {
            loadTierData()
            loadTrendsData()
          }}
          disabled={loading}
          className="flex items-center space-x-2 bg-tft-gold/20 text-tft-gold px-4 py-2 rounded-lg hover:bg-tft-gold/30 disabled:opacity-50 transition-colors duration-200"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Quick Stats */}
      {tierData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center space-x-2">
              <Trophy className="w-5 h-5 text-tft-gold" />
              <span className="text-gray-400">Total Compositions</span>
            </div>
            <div className="text-2xl font-bold text-white mt-1">
              {tierData.total_compositions}
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-blue-400" />
              <span className="text-gray-400">Last Updated</span>
            </div>
            <div className="text-sm text-white mt-1">
              {tierData.last_updated}
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-green-400" />
              <span className="text-gray-400">Data Source</span>
            </div>
            <div className="text-sm text-white mt-1">
              {tierData.data_source}
            </div>
          </div>
        </div>
      )}

      {/* Tier Filter */}
      <div className="flex flex-wrap gap-2">
        {tierOrder.map((tier) => (
          <button
            key={tier}
            onClick={() => setSelectedTier(tier)}
            className={`px-4 py-2 rounded-lg border transition-colors duration-200 ${
              selectedTier === tier
                ? tierColors[tier]
                : 'text-gray-400 bg-gray-800/30 border-gray-600 hover:bg-gray-700/50'
            }`}
          >
            {tier === 'ALL' ? 'All Tiers' : `${tier} Tier`}
          </button>
        ))}
      </div>

      {/* Trends Section */}
      {trendsData && (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center space-x-2 mb-4">
            <TrendingUp className="w-5 h-5 text-tft-gold" />
            <h3 className="text-xl font-bold text-white">Recent Trends</h3>
            <span className="text-sm text-gray-400">
              ({trendsData.parameters.days_analyzed} days)
            </span>
          </div>
          <div className="bg-gray-900/50 rounded-lg p-4">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
              {trendsData.trends_analysis}
            </pre>
          </div>
        </div>
      )}

      {/* Compositions List */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700">
        <div className="p-6">
          <h3 className="text-xl font-bold text-white mb-4">
            Compositions {selectedTier !== 'ALL' && `- ${selectedTier} Tier`}
          </h3>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-8 h-8 text-tft-gold animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {getFilteredCompositions().map((comp, index) => (
                <div
                  key={`${comp.name}-${index}`}
                  className="bg-gray-900/50 rounded-lg border border-gray-600 overflow-hidden"
                >
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-800/50 transition-colors duration-200"
                    onClick={() => toggleCompExpanded(comp.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold border ${tierColors[comp.tier as TierFilter]}`}>
                          {comp.tier}
                        </span>
                        <h4 className="font-bold text-white text-lg">{comp.name}</h4>
                        <span className="text-sm text-gray-400">{comp.primary_trait}</span>
                      </div>

                      <div className="flex items-center space-x-6">
                        <div className="text-center">
                          <div className="text-xs text-gray-400">Win Rate</div>
                          <div className="text-green-400 font-bold">
                            {formatWinRate(comp.win_rate)}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-gray-400">Avg Place</div>
                          <div className="text-yellow-400 font-bold">
                            {formatPlacement(comp.avg_placement)}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-xs text-gray-400">Play Rate</div>
                          <div className="text-blue-400 font-bold">
                            {formatPlayRate(comp.play_rate)}
                          </div>
                        </div>
                        {expandedComps.has(comp.name) ? (
                          <ChevronUp className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {expandedComps.has(comp.name) && (
                    <div className="px-4 pb-4 border-t border-gray-700">
                      <div className="pt-4">
                        <div className="text-sm text-gray-400 mb-2">Key Champions:</div>
                        <div className="flex flex-wrap gap-2">
                          {comp.key_champions.map((champion) => (
                            <span
                              key={champion}
                              className="bg-tft-gold/20 text-tft-gold px-3 py-1 rounded-full text-sm font-medium"
                            >
                              {champion}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {getFilteredCompositions().length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  No compositions found for the selected tier.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}