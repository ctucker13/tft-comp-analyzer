'use client'

import { useState } from 'react'
import { MessageSquare, BarChart3, Database, Brain, Sparkles } from 'lucide-react'
import ChatInterface from '@/components/ChatInterface'
import MetaAnalysis from '@/components/MetaAnalysis'
import DatabaseExplorer from '@/components/DatabaseExplorer'
import MLRecommendations from '@/components/MLRecommendations'

type ActiveTab = 'chat' | 'meta' | 'database' | 'ml'

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('chat')

  const tabs = [
    { id: 'chat' as ActiveTab, label: 'AI Strategic Chat', icon: MessageSquare, description: 'Get personalized strategic advice' },
    { id: 'meta' as ActiveTab, label: 'Meta Analysis', icon: BarChart3, description: 'Current tier lists and trends' },
    { id: 'database' as ActiveTab, label: 'Champion Database', icon: Database, description: 'Explore champions and traits' },
    { id: 'ml' as ActiveTab, label: 'ML Recommendations', icon: Brain, description: 'Strategic decision making' },
  ]

  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatInterface />
      case 'meta':
        return <MetaAnalysis />
      case 'database':
        return <DatabaseExplorer />
      case 'ml':
        return <MLRecommendations />
      default:
        return <ChatInterface />
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-tft-gold" />
              <h1 className="text-2xl font-bold tft-gradient">
                TFT Composition Analyzer
              </h1>
            </div>
            <div className="text-sm text-gray-400">
              Set 15: K.O. Coliseum
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-gray-800 bg-black/10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                    ${activeTab === tab.id
                      ? 'border-tft-gold text-tft-gold'
                      : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                    }
                    transition-colors duration-200
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Tab Description */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <p className="text-gray-400 text-sm">
          {tabs.find(tab => tab.id === activeTab)?.description}
        </p>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
        {renderActiveComponent()}
      </main>
    </div>
  )
}