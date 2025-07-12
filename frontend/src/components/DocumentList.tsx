'use client'

import React from 'react'
import { DocumentIcon, TrashIcon, CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline'

interface Document {
  id: string
  filename: string
  status: 'processing' | 'completed' | 'failed'
  total_pages: number
  total_chunks: number
  uploaded_at: string
  processed_at?: string
}

interface DocumentListProps {
  documents: Document[]
  onDelete: (documentId: string) => void
}

export const DocumentList: React.FC<DocumentListProps> = ({ documents, onDelete }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-yellow-500 animate-pulse" />
      case 'failed':
        return <div className="h-5 w-5 rounded-full bg-red-500"></div>
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed'
      case 'processing':
        return 'Processing...'
      case 'failed':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (documents.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Documents</h2>
        <div className="text-center py-8">
          <DocumentIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No documents uploaded yet</p>
          <p className="text-sm text-gray-400 mt-1">Upload a PDF to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">
        Documents ({documents.length})
      </h2>
      
      <div className="space-y-3">
        {documents.map((doc) => (
          <div key={doc.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1">
                <DocumentIcon className="h-8 w-8 text-blue-500 flex-shrink-0" />
                
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {doc.filename}
                  </h3>
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      {getStatusIcon(doc.status)}
                      <span>{getStatusText(doc.status)}</span>
                    </div>
                    <span>{doc.total_pages} pages</span>
                    {doc.total_chunks > 0 && (
                      <span>{doc.total_chunks} chunks</span>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2 ml-4">
                <div className="text-right text-sm text-gray-500">
                  <p>Uploaded: {formatDate(doc.uploaded_at)}</p>
                  {doc.processed_at && (
                    <p>Processed: {formatDate(doc.processed_at)}</p>
                  )}
                </div>
                
                <button
                  onClick={() => onDelete(doc.id)}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  title="Delete document"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
} 