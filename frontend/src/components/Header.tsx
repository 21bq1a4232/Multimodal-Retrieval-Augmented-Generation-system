'use client'

import React from 'react'
import { CpuChipIcon, SparklesIcon } from '@heroicons/react/24/outline'

export const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <SparklesIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Multimodal RAG System
              </h1>
              <p className="text-sm text-gray-500">
                Production-grade document intelligence
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>System Online</span>
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <CpuChipIcon className="h-4 w-4" />
              <span>Ollama LLM</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
} 