import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Brain, Upload, Search, FileText, Activity, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';
import toast from 'react-hot-toast';

interface SystemStats {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  avg_response_time: number;
  system_status: string;
}

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiService.getSystemStats();
        setStats(data);
      } catch (error) {
        toast.error('Failed to load system statistics');
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const quickActions = [
    {
      title: 'Upload Document',
      description: 'Add new PDF documents to the knowledge base',
      icon: Upload,
      path: '/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'Ask Questions',
      description: 'Query your documents with natural language',
      icon: Search,
      path: '/query',
      color: 'bg-green-500',
    },
    {
      title: 'View Documents',
      description: 'Browse and manage uploaded documents',
      icon: FileText,
      path: '/documents',
      color: 'bg-purple-500',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.username}!
        </h1>
        <p className="text-gray-600">
          Your Multimodal RAG System is ready to help you find answers in your documents.
        </p>
      </div>

      {/* System Status */}
      {stats && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">System Status</h2>
            <div className="flex items-center space-x-2">
              {getStatusIcon(stats.system_status)}
              <span className="text-sm font-medium text-gray-700">
                {stats.system_status}
              </span>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <FileText className="h-6 w-6 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Documents</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_documents}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <Brain className="h-6 w-6 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Chunks</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_chunks}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <Search className="h-6 w-6 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600">Queries</p>
                <p className="text-lg font-semibold text-gray-900">{stats.total_queries}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
              <Clock className="h-6 w-6 text-orange-600" />
              <div>
                <p className="text-sm text-gray-600">Avg Response</p>
                <p className="text-lg font-semibold text-gray-900">{stats.avg_response_time}ms</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.path}
                to={action.path}
                className="group block p-6 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-all duration-200 hover:border-primary-300"
              >
                <div className="flex items-center space-x-4">
                  <div className={`p-3 rounded-lg ${action.color} text-white`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-200">
                      {action.title}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {action.description}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h2>
        <div className="space-y-4">
          <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
            <Activity className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">System is running smoothly</p>
              <p className="text-xs text-gray-600">All services are operational</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
            <Upload className="h-5 w-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Ready for document uploads</p>
              <p className="text-xs text-gray-600">PDF files up to 50MB supported</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
            <Search className="h-5 w-5 text-purple-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">Query system active</p>
              <p className="text-xs text-gray-600">Ask questions about your documents</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 