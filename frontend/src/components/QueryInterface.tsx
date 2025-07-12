'use client'

import React, { useState } from 'react'
import { MagnifyingGlassIcon, SparklesIcon } from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'

interface QueryResult {
  answer: string
  confidence: number
  citations: Array<{
    reference_id: string
    content: string
    content_type: string
    page_number: number
    score: number
  }>
  metadata: {
    query: string
    total_time_ms: number
    chunks_used: number
    model_used: string
  }
}

interface QueryInterfaceProps {
  onQuery: (query: string) => Promise<QueryResult>
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ onQuery }) => {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return

    setIsLoading(true)
    try {
      const result = await onQuery(query)
      setResult(result)
    } catch (error) {
      console.error('Query failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Query Documents</h2>
      
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="w-full p-4 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-2 top-2 p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <MagnifyingGlassIcon className="h-5 w-5" />
            )}
          </button>
        </div>
      </form>

      {result && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center mb-3">
              <SparklesIcon className="h-5 w-5 text-blue-500 mr-2" />
              <h3 className="text-lg font-medium text-gray-800">Answer</h3>
              <span className="ml-auto text-sm text-gray-500">
                Confidence: {Math.round(result.confidence * 100)}%
              </span>
            </div>
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {/* Citations */}
          {result.citations.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Sources</h3>
              <div className="space-y-3">
                {result.citations.map((citation, index) => (
                  <div key={citation.reference_id} className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-blue-600">
                        [{citation.reference_id}] {citation.content_type.toUpperCase()}
                      </span>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <span>Page {citation.page_number}</span>
                        <span>•</span>
                        <span>Score: {Math.round(citation.score * 100)}%</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {citation.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Response Time</span>
                <p className="font-medium">{result.metadata.total_time_ms}ms</p>
              </div>
              <div>
                <span className="text-gray-500">Chunks Used</span>
                <p className="font-medium">{result.metadata.chunks_used}</p>
              </div>
              <div>
                <span className="text-gray-500">Model</span>
                <p className="font-medium">{result.metadata.model_used}</p>
              </div>
              <div>
                <span className="text-gray-500">Confidence</span>
                <p className="font-medium">{Math.round(result.confidence * 100)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
} 