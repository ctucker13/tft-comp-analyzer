'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import type { ChatRequest, ChatResponse } from '@/types/api'

interface Message {
  id: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
  intent?: string
  tool_used?: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your TFT strategic advisor. Ask me about team compositions, meta trends, or strategic decisions!',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const request: ChatRequest = {
        message: inputMessage,
        conversation_id: conversationId,
        provider: 'anthropic',
      }

      const response = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ChatResponse = await response.json()

      if (!conversationId) {
        setConversationId(data.conversation_id)
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        sender: 'assistant',
        timestamp: new Date(),
        intent: data.intent,
        tool_used: data.tool_used,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I'm having trouble connecting to my backend systems. Here's some quick TFT advice while I work on reconnecting:

**If you're asking about strategy:** Focus on flexible play, strong economies, and positioning. Prioritize board strength early game.

**If you're asking about meta:** Mighty Mech, Star Guardian, and Soul Fighter are generally strong compositions in Set 15.

Please try your message again in a moment!`,
        sender: 'assistant',
        timestamp: new Date(),
        intent: 'error_fallback',
        tool_used: 'frontend_fallback'
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[600px] bg-gray-900/50 rounded-lg border border-gray-700">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start space-x-3 ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.sender === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 bg-tft-gold/20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-tft-gold" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white ml-auto'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* Show tool/intent info for assistant messages */}
              {message.sender === 'assistant' && (message.tool_used || message.intent) && (
                <div className="mt-2 text-xs text-gray-400 border-t border-gray-700 pt-2">
                  {message.intent && (
                    <span className="inline-block bg-gray-700 px-2 py-1 rounded mr-2">
                      Intent: {message.intent}
                    </span>
                  )}
                  {message.tool_used && (
                    <span className="inline-block bg-gray-700 px-2 py-1 rounded">
                      Tool: {message.tool_used}
                    </span>
                  )}
                </div>
              )}
            </div>

            {message.sender === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600/20 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-blue-400" />
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-start space-x-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 bg-tft-gold/20 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-tft-gold" />
            </div>
            <div className="bg-gray-800 rounded-lg px-4 py-2">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 text-tft-gold animate-spin" />
                <span className="text-sm text-gray-400">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about TFT strategy, meta trends, compositions..."
            className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-tft-gold focus:border-transparent resize-none min-h-[40px] max-h-[120px]"
            rows={1}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="bg-tft-gold text-black px-4 py-2 rounded-lg hover:bg-tft-gold/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center justify-center min-w-[48px]"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Usage hints */}
        <div className="mt-2 text-xs text-gray-500">
          Try asking: "What are the best S-tier comps?" or "I have 30 gold at level 6, what should I do?"
        </div>
      </div>
    </div>
  )
}