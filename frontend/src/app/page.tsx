'use client'

import React, { useState, useEffect } from 'react'
import { DocumentUpload } from '@/components/DocumentUpload'
import { QueryInterface } from '@/components/QueryInterface'
import { DocumentList } from '@/components/DocumentList'
import { SystemStats } from '@/components/SystemStats'
import { Header } from '@/components/Header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { FileText, MessageSquare, BarChart3, Upload } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export default function Home() {
  const [activeTab, setActiveTab] = useState('upload')
  const [documents, setDocuments] = useState([])
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  // Fetch documents and stats
  useEffect(() => {
    fetchDocuments()
    fetchStats()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`)
      setDocuments(response.data.documents || [])
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const handleUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE_URL}/documents/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      // Refresh documents list
      fetchDocuments()
      
      // Switch to documents tab to show upload result
      setActiveTab('documents')
      
      return response.data
    } catch (error) {
      console.error('Upload failed:', error)
      throw error
    }
  }

  const handleQuery = async (query: string) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, { query })
      return response.data
    } catch (error) {
      console.error('Query failed:', error)
      throw error
    }
  }

  const handleDelete = async (documentId: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/documents/${documentId}`)
      fetchDocuments()
    } catch (error) {
      console.error('Delete failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Multimodal RAG System
          </h1>
          <p className="text-lg text-gray-600">
            Upload documents, ask questions, and get intelligent answers with citations
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="query" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Query
            </TabsTrigger>
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Statistics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Document Upload</CardTitle>
                <CardDescription>
                  Upload PDF documents to add them to your knowledge base
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentUpload onUpload={handleUpload} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="query" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Ask Questions</CardTitle>
                <CardDescription>
                  Ask questions about your uploaded documents and get intelligent answers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <QueryInterface onQuery={handleQuery} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Document Library</CardTitle>
                <CardDescription>
                  Manage your uploaded documents and view processing status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentList documents={documents} onDelete={handleDelete} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stats" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>System Statistics</CardTitle>
                <CardDescription>
                  View system performance metrics and usage statistics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SystemStats stats={stats} isLoading={isLoading} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
} 