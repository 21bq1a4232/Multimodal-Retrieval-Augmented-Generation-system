'use client'

import React from 'react'
import { 
  DocumentTextIcon, 
  CpuChipIcon, 
  ClockIcon, 
  SparklesIcon,
  ChartBarIcon,
  ServerIcon
} from '@heroicons/react/24/outline'

interface SystemStats {
  system_stats: {
    total_documents: number
    total_chunks: number
    processed_documents: number
    embedding_model: string
    llm_model: string
    vector_db: string
    demo_mode: boolean
  }
  performance_metrics: {
    avg_response_time_ms: number
    avg_confidence: number
    retrieval_accuracy: number
  }
}

interface SystemStatsProps {
  stats: SystemStats | null
  isLoading: boolean
}

export const SystemStats: React.FC<SystemStatsProps> = ({ stats, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">System Statistics</h2>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">System Statistics</h2>
        <p className="text-gray-500">Unable to load statistics</p>
      </div>
    )
  }

  const formatPercentage = (value: number) => `${Math.round(value * 100)}%`

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-800">System Statistics</h2>
        {stats.system_stats.demo_mode && (
          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
            Demo Mode
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Document Stats */}
        <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <DocumentTextIcon className="h-8 w-8 text-blue-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-800">Documents</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total</span>
              <span className="font-medium">{stats.system_stats.total_documents}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Processed</span>
              <span className="font-medium">{stats.system_stats.processed_documents}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Chunks</span>
              <span className="font-medium">{stats.system_stats.total_chunks}</span>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <ChartBarIcon className="h-8 w-8 text-green-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-800">Performance</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Response</span>
              <span className="font-medium">{stats.performance_metrics.avg_response_time_ms}ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Confidence</span>
              <span className="font-medium">{formatPercentage(stats.performance_metrics.avg_confidence)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Retrieval Accuracy</span>
              <span className="font-medium">{formatPercentage(stats.performance_metrics.retrieval_accuracy)}</span>
            </div>
          </div>
        </div>

        {/* System Configuration */}
        <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <ServerIcon className="h-8 w-8 text-purple-600 mr-3" />
            <h3 className="text-lg font-medium text-gray-800">Configuration</h3>
          </div>
          <div className="space-y-2">
            <div>
              <span className="text-sm text-gray-600 block">LLM Model</span>
              <span className="font-medium text-sm">{stats.system_stats.llm_model}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600 block">Vector DB</span>
              <span className="font-medium text-sm">{stats.system_stats.vector_db}</span>
            </div>
            <div>
              <span className="text-sm text-gray-600 block">Embedding Model</span>
              <span className="font-medium text-sm truncate" title={stats.system_stats.embedding_model}>
                {stats.system_stats.embedding_model.split('/').pop()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <ClockIcon className="h-6 w-6 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Response Time</p>
          <p className="text-lg font-semibold">{stats.performance_metrics.avg_response_time_ms}ms</p>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <SparklesIcon className="h-6 w-6 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Confidence</p>
          <p className="text-lg font-semibold">{formatPercentage(stats.performance_metrics.avg_confidence)}</p>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <ChartBarIcon className="h-6 w-6 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Accuracy</p>
          <p className="text-lg font-semibold">{formatPercentage(stats.performance_metrics.retrieval_accuracy)}</p>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <CpuChipIcon className="h-6 w-6 text-gray-600 mx-auto mb-2" />
          <p className="text-sm text-gray-600">Processing</p>
          <p className="text-lg font-semibold">
            {stats.system_stats.processed_documents}/{stats.system_stats.total_documents}
          </p>
        </div>
      </div>
    </div>
  )
} 