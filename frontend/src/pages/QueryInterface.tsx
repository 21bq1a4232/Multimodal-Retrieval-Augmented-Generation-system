import React, { useState } from 'react';
import { Send, ThumbsUp, ThumbsDown, Copy, ExternalLink } from 'lucide-react';
import { apiService, QueryResponse } from '../services/apiService';
import toast from 'react-hot-toast';

interface QueryHistory {
  id: string;
  query: string;
  response: QueryResponse;
  timestamp: Date;
}

const QueryInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null);
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const response = await apiService.queryDocuments({ query: query.trim() });
      setCurrentResponse(response);
      
      const historyItem: QueryHistory = {
        id: Math.random().toString(36).substr(2, 9),
        query: query.trim(),
        response,
        timestamp: new Date(),
      };
      
      setQueryHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10
      setQuery('');
    } catch (error) {
      toast.error('Failed to get response. Please try again.');
      console.error('Query error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (queryId: string, helpful: boolean) => {
    try {
      await apiService.submitFeedback({
        query_id: queryId,
        helpful,
      });
      toast.success('Thank you for your feedback!');
    } catch (error) {
      toast.error('Failed to submit feedback');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Ask Questions</h1>
        <p className="text-gray-600">
          Ask questions about your uploaded documents and get AI-powered answers with citations.
        </p>
      </div>

      {/* Query Form */}
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="input-field h-24 resize-none"
              disabled={isLoading}
            />
          </div>
          
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  <span>Ask Question</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Current Response */}
      {currentResponse && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Latest Response</h2>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">
                Confidence: {formatConfidence(currentResponse.confidence)}
              </span>
              <button
                onClick={() => copyToClipboard(currentResponse.answer)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                title="Copy answer"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="prose max-w-none">
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="text-gray-900 whitespace-pre-wrap">{currentResponse.answer}</p>
            </div>

            {currentResponse.citations && currentResponse.citations.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Sources</h3>
                <div className="space-y-3">
                  {currentResponse.citations.map((citation, index) => (
                    <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-gray-900 mb-1">{citation.content}</p>
                          <p className="text-xs text-gray-600">
                            Source: {citation.source}
                            {citation.page && ` (Page ${citation.page})`}
                          </p>
                        </div>
                        <button
                          onClick={() => copyToClipboard(citation.content)}
                          className="text-blue-400 hover:text-blue-600 transition-colors duration-200 ml-2"
                          title="Copy citation"
                        >
                          <Copy className="h-3 w-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center space-x-4 mt-6 pt-4 border-t border-gray-200">
              <span className="text-sm text-gray-600">Was this helpful?</span>
              <button
                onClick={() => handleFeedback('current', true)}
                className="flex items-center space-x-1 text-green-600 hover:text-green-700 transition-colors duration-200"
              >
                <ThumbsUp className="h-4 w-4" />
                <span className="text-sm">Yes</span>
              </button>
              <button
                onClick={() => handleFeedback('current', false)}
                className="flex items-center space-x-1 text-red-600 hover:text-red-700 transition-colors duration-200"
              >
                <ThumbsDown className="h-4 w-4" />
                <span className="text-sm">No</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Query History */}
      {queryHistory.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Questions</h2>
          <div className="space-y-4">
            {queryHistory.map((item) => (
              <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{item.query}</h3>
                  <span className="text-xs text-gray-500">
                    {item.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {item.response.answer}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-xs text-gray-500">
                      Confidence: {formatConfidence(item.response.confidence)}
                    </span>
                    {item.response.citations && (
                      <span className="text-xs text-gray-500">
                        {item.response.citations.length} source{item.response.citations.length !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleFeedback(item.id, true)}
                      className="text-gray-400 hover:text-green-600 transition-colors duration-200"
                      title="Helpful"
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => handleFeedback(item.id, false)}
                      className="text-gray-400 hover:text-red-600 transition-colors duration-200"
                      title="Not helpful"
                    >
                      <ThumbsDown className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Tips for Better Results</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <div className="bg-blue-100 rounded-full p-2">
              <span className="text-blue-600 text-sm font-bold">1</span>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Be Specific</h3>
              <p className="text-sm text-gray-600">
                Ask specific questions rather than general ones for more accurate answers
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="bg-green-100 rounded-full p-2">
              <span className="text-green-600 text-sm font-bold">2</span>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Use Keywords</h3>
              <p className="text-sm text-gray-600">
                Include relevant keywords from your documents in your questions
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="bg-purple-100 rounded-full p-2">
              <span className="text-purple-600 text-sm font-bold">3</span>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Check Sources</h3>
              <p className="text-sm text-gray-600">
                Always review the provided sources to verify the information
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="bg-orange-100 rounded-full p-2">
              <span className="text-orange-600 text-sm font-bold">4</span>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-1">Provide Feedback</h3>
              <p className="text-sm text-gray-600">
                Rate responses to help improve the system's accuracy
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryInterface; 