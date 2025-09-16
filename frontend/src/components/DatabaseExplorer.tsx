'use client'

import { useState, useEffect } from 'react'
import { Search, Star, Users, Filter, RefreshCw } from 'lucide-react'
import type { Champion, ChampionFilter, DatabaseResponse } from '@/types/api'

export default function DatabaseExplorer() {
  const [champions, setChampions] = useState<Champion[]>([])
  const [filteredChampions, setFilteredChampions] = useState<Champion[]>([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState<ChampionFilter>({})
  const [selectedCost, setSelectedCost] = useState<number | null>(null)
  const [selectedTrait, setSelectedTrait] = useState<string>('')

  const costs = [1, 2, 3, 4, 5]
  const costColors = {
    1: 'text-gray-400 bg-gray-900/20 border-gray-500/30',
    2: 'text-green-400 bg-green-900/20 border-green-500/30',
    3: 'text-blue-400 bg-blue-900/20 border-blue-500/30',
    4: 'text-purple-400 bg-purple-900/20 border-purple-500/30',
    5: 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30'
  }

  useEffect(() => {
    loadChampions()
  }, [])

  useEffect(() => {
    applyFilters()
  }, [champions, searchTerm, selectedCost, selectedTrait])

  const loadChampions = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/database/champions?limit=100')
      if (response.ok) {
        const data: DatabaseResponse = await response.json()
        setChampions(data.champions || [])
      }
    } catch (error) {
      console.error('Error loading champions:', error)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = [...champions]

    // Text search
    if (searchTerm) {
      filtered = filtered.filter(champion =>
        champion.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        champion.traits.some(trait => trait.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Cost filter
    if (selectedCost) {
      filtered = filtered.filter(champion => champion.cost === selectedCost)
    }

    // Trait filter
    if (selectedTrait) {
      filtered = filtered.filter(champion =>
        champion.traits.some(trait => trait.toLowerCase().includes(selectedTrait.toLowerCase()))
      )
    }

    setFilteredChampions(filtered)
  }

  const clearFilters = () => {
    setSearchTerm('')
    setSelectedCost(null)
    setSelectedTrait('')
  }

  // Get unique traits from all champions
  const getAllTraits = (): string[] => {
    const traits = new Set<string>()
    champions.forEach(champion => {
      champion.traits.forEach(trait => traits.add(trait))
    })
    return Array.from(traits).sort()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Champion Database</h2>
          <p className="text-gray-400">
            Explore all champions, traits, and synergies in Set 15
          </p>
        </div>
        <button
          onClick={loadChampions}
          disabled={loading}
          className="flex items-center space-x-2 bg-tft-gold/20 text-tft-gold px-4 py-2 rounded-lg hover:bg-tft-gold/30 disabled:opacity-50 transition-colors duration-200"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-tft-gold" />
            <span className="text-gray-400">Total Champions</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {champions.length}
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center space-x-2">
            <Star className="w-5 h-5 text-blue-400" />
            <span className="text-gray-400">Total Traits</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {getAllTraits().length}
          </div>
        </div>

        <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-green-400" />
            <span className="text-gray-400">Filtered Results</span>
          </div>
          <div className="text-2xl font-bold text-white mt-1">
            {filteredChampions.length}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Filters</h3>
          <button
            onClick={clearFilters}
            className="text-sm text-gray-400 hover:text-white transition-colors duration-200"
          >
            Clear All
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search champions or traits..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-900 text-white rounded-lg pl-10 pr-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
          />
        </div>

        {/* Cost Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Cost
          </label>
          <div className="flex flex-wrap gap-2">
            {costs.map((cost) => (
              <button
                key={cost}
                onClick={() => setSelectedCost(selectedCost === cost ? null : cost)}
                className={`px-3 py-1 rounded-lg border text-sm font-bold transition-colors duration-200 ${
                  selectedCost === cost
                    ? costColors[cost as keyof typeof costColors]
                    : 'text-gray-400 bg-gray-900/30 border-gray-600 hover:bg-gray-700/50'
                }`}
              >
                {cost}⭐
              </button>
            ))}
          </div>
        </div>

        {/* Trait Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Trait
          </label>
          <select
            value={selectedTrait}
            onChange={(e) => setSelectedTrait(e.target.value)}
            className="w-full md:w-64 bg-gray-900 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
          >
            <option value="">All Traits</option>
            {getAllTraits().map((trait) => (
              <option key={trait} value={trait}>
                {trait}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Champions Grid */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-6">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-8 h-8 text-tft-gold animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredChampions.map((champion, index) => (
              <div
                key={`${champion.name}-${index}`}
                className="bg-gray-900/50 rounded-lg p-4 border border-gray-600 hover:border-tft-gold/50 transition-colors duration-200"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-bold text-white text-lg">{champion.name}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${
                    costColors[champion.cost as keyof typeof costColors]
                  }`}>
                    {champion.cost}⭐
                  </span>
                </div>

                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-gray-400">Type:</span>
                    <span className="text-sm text-white ml-2">{champion.type}</span>
                  </div>

                  <div>
                    <span className="text-xs text-gray-400 mb-1 block">Traits:</span>
                    <div className="flex flex-wrap gap-1">
                      {champion.traits.map((trait) => (
                        <span
                          key={trait}
                          className="bg-tft-gold/20 text-tft-gold px-2 py-1 rounded text-xs font-medium"
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && filteredChampions.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            No champions found matching your filters.
          </div>
        )}
      </div>
    </div>
  )
}