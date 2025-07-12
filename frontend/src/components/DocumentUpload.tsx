'use client'

import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { ArrowUpTrayIcon, DocumentIcon } from '@heroicons/react/24/outline'

interface DocumentUploadProps {
  onUpload: (file: File) => void
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUpload }) => {
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      setIsUploading(true)
      
      try {
        await onUpload(file)
      } finally {
        setIsUploading(false)
      }
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    disabled: isUploading
  })

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Upload Document</h2>
      
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-4">
          {isUploading ? (
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          ) : (
            <ArrowUpTrayIcon className="h-12 w-12 text-gray-400" />
          )}
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {isUploading ? 'Uploading...' : 'Drop your PDF here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {isUploading ? 'Processing your document...' : 'or click to select a file'}
            </p>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <DocumentIcon className="h-4 w-4" />
            <span>PDF files only</span>
          </div>
        </div>
      </div>
    </div>
  )
} 