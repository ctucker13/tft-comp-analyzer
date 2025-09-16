'use client'

import { useState } from 'react'
import { Brain, Zap, TrendingUp, Play, RotateCcw } from 'lucide-react'
import type { MLRecommendationRequest, MLRecommendationResponse } from '@/types/api'

interface GameStateForm {
  gold: number
  level: number
  stage: number
  health: number
}

const exampleScenarios = [
  {
    name: 'Early Game Economy',
    description: 'Should I roll or level with decent economy?',
    state: { gold: 30, level: 6, stage: 3, health: 85 }
  },
  {
    name: 'Mid Game Transition',
    description: 'High gold, should I push level 8 or stabilize?',
    state: { gold: 45, level: 7, stage: 4, health: 70 }
  },
  {
    name: 'Late Game All-In',
    description: 'Low health, need to find upgrades fast',
    state: { gold: 25, level: 8, stage: 6, health: 30 }
  },
  {
    name: 'Win Streak Power',
    description: 'High health and gold, optimize win streak',
    state: { gold: 60, level: 7, stage: 4, health: 95 }
  }
]

export default function MLRecommendations() {
  const [gameState, setGameState] = useState<GameStateForm>({
    gold: 30,
    level: 6,
    stage: 3,
    health: 85
  })
  const [recommendation, setRecommendation] = useState<MLRecommendationResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const handleInputChange = (field: keyof GameStateForm, value: number) => {
    setGameState(prev => ({ ...prev, [field]: value }))
  }

  const loadScenario = (scenario: typeof exampleScenarios[0]) => {
    setGameState(scenario.state)
    setRecommendation(null)
  }

  const getRecommendation = async () => {
    setLoading(true)
    try {
      const request: MLRecommendationRequest = {
        ...gameState,
        round_number: gameState.stage * 7 // Approximate round number
      }

      const response = await fetch('http://localhost:8000/api/ml/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (response.ok) {
        const data = await response.json()
        setRecommendation(data)
      } else {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
    } catch (error) {
      console.error('Error getting ML recommendation:', error)
      setRecommendation({
        recommendation: 'Error: Unable to get ML recommendation. Please make sure the backend server is running.',
        game_state: {
          ...gameState,
          game_phase: 'unknown'
        },
        confidence: 0,
        analysis_type: 'Error'
      })
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setGameState({ gold: 30, level: 6, stage: 3, health: 85 })
    setRecommendation(null)
  }

  const getGamePhaseColor = (phase: string) => {
    switch (phase.toLowerCase()) {
      case 'early': return 'text-green-400 bg-green-900/20 border-green-500/30'
      case 'mid': return 'text-yellow-400 bg-yellow-900/20 border-yellow-500/30'
      case 'late': return 'text-red-400 bg-red-900/20 border-red-500/30'
      default: return 'text-gray-400 bg-gray-900/20 border-gray-500/30'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-400'
    if (confidence >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">ML Recommendations</h2>
        <p className="text-gray-400">
          Get AI-powered strategic recommendations based on your current game state
        </p>
      </div>

      {/* Example Scenarios */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-bold text-white mb-4">Quick Scenarios</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exampleScenarios.map((scenario) => (
            <div
              key={scenario.name}
              className="bg-gray-900/50 rounded-lg p-4 border border-gray-600 hover:border-tft-gold/50 cursor-pointer transition-colors duration-200"
              onClick={() => loadScenario(scenario)}
            >
              <h4 className="font-bold text-white mb-2">{scenario.name}</h4>
              <p className="text-sm text-gray-400 mb-3">{scenario.description}</p>
              <div className="text-xs text-gray-500">
                Gold: {scenario.state.gold} | Level: {scenario.state.level} |
                Stage: {scenario.state.stage} | Health: {scenario.state.health}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Game State Input */}
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Current Game State</h3>
          <button
            onClick={resetForm}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* Gold */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Gold
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={gameState.gold}
              onChange={(e) => handleInputChange('gold', parseInt(e.target.value) || 0)}
              className="w-full bg-gray-900 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
            />
          </div>

          {/* Level */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Level
            </label>
            <input
              type="number"
              min="1"
              max="11"
              value={gameState.level}
              onChange={(e) => handleInputChange('level', parseInt(e.target.value) || 1)}
              className="w-full bg-gray-900 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
            />
          </div>

          {/* Stage */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Stage
            </label>
            <input
              type="number"
              min="1"
              max="7"
              value={gameState.stage}
              onChange={(e) => handleInputChange('stage', parseInt(e.target.value) || 1)}
              className="w-full bg-gray-900 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
            />
          </div>

          {/* Health */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Health
            </label>
            <input
              type="number"
              min="0"
              max="100"
              value={gameState.health}
              onChange={(e) => handleInputChange('health', parseInt(e.target.value) || 0)}
              className="w-full bg-gray-900 text-white rounded-lg px-3 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent"
            />
          </div>
        </div>

        <button
          onClick={getRecommendation}
          disabled={loading}
          className="w-full md:w-auto flex items-center justify-center space-x-2 bg-tft-gold text-black px-6 py-3 rounded-lg hover:bg-tft-gold/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {loading ? (
            <>
              <Brain className="w-5 h-5 animate-pulse" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Get ML Recommendation</span>
            </>
          )}
        </button>
      </div>

      {/* Recommendation Results */}
      {recommendation && (
        <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700 space-y-4">
          <div className="flex items-center space-x-2">
            <Brain className="w-6 h-6 text-tft-gold" />
            <h3 className="text-xl font-bold text-white">Strategic Recommendation</h3>
          </div>

          {/* Game Phase and Confidence */}
          <div className="flex items-center space-x-4">
            <span className={`px-3 py-1 rounded-lg text-sm font-bold border ${getGamePhaseColor(recommendation.game_state.game_phase)}`}>
              {recommendation.game_state.game_phase.toUpperCase()} GAME
            </span>
            <span className="text-gray-400">
              Confidence:
              <span className={`ml-1 font-bold ${getConfidenceColor(recommendation.confidence)}`}>
                {(recommendation.confidence * 100).toFixed(0)}%
              </span>
            </span>
            <span className="text-gray-400">
              Analysis: <span className="text-white">{recommendation.analysis_type}</span>
            </span>
          </div>

          {/* Current Game State Summary */}
          <div className="bg-gray-900/50 rounded-lg p-4">
            <div className="text-sm text-gray-400 mb-2">Current State:</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Gold:</span>
                <span className="text-white ml-1 font-bold">{recommendation.game_state.gold}</span>
              </div>
              <div>
                <span className="text-gray-400">Level:</span>
                <span className="text-white ml-1 font-bold">{recommendation.game_state.level}</span>
              </div>
              <div>
                <span className="text-gray-400">Stage:</span>
                <span className="text-white ml-1 font-bold">{recommendation.game_state.stage}</span>
              </div>
              <div>
                <span className="text-gray-400">Health:</span>
                <span className="text-white ml-1 font-bold">{recommendation.game_state.health}</span>
              </div>
            </div>
          </div>

          {/* Main Recommendation */}
          <div className="bg-gradient-to-r from-tft-gold/10 to-transparent rounded-lg p-4 border border-tft-gold/30">
            <div className="flex items-start space-x-3">
              <Zap className="w-5 h-5 text-tft-gold mt-1 flex-shrink-0" />
              <div>
                <div className="text-sm text-gray-400 mb-1">Recommendation:</div>
                <pre className="text-white whitespace-pre-wrap font-mono text-sm leading-relaxed">
                  {recommendation.recommendation}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ML Training Info */}
      <div className="bg-blue-900/20 rounded-lg p-4 border border-blue-500/30">
        <div className="flex items-start space-x-3">
          <TrendingUp className="w-5 h-5 text-blue-400 mt-1 flex-shrink-0" />
          <div className="text-sm text-blue-100">
            <div className="font-bold mb-1">About ML Recommendations</div>
            <p>
              Our ML model analyzes thousands of high-rank TFT matches to provide strategic recommendations.
              It considers game phase, economy, positioning, and current meta trends to suggest optimal plays.
              The model is retrained daily with fresh challenger-tier match data for maximum relevance.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}