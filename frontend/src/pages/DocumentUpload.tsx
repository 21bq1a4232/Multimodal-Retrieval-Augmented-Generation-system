import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';
import { apiService } from '../services/apiService';
import toast from 'react-hot-toast';

interface UploadStatus {
  id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress?: number;
  error?: string;
}

const DocumentUpload: React.FC = () => {
  const [uploads, setUploads] = useState<UploadStatus[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error(`${file.name} is not a PDF file`);
        continue;
      }

      const uploadId = Math.random().toString(36).substr(2, 9);
      const newUpload: UploadStatus = {
        id: uploadId,
        filename: file.name,
        status: 'uploading',
        progress: 0,
      };

      setUploads(prev => [...prev, newUpload]);

      try {
        // Upload file
        const response = await apiService.uploadDocument(file);
        
        setUploads(prev => prev.map(upload => 
          upload.id === uploadId 
            ? { ...upload, status: 'processing' as const, progress: 50 }
            : upload
        ));

        // Poll for status
        const pollStatus = async () => {
          try {
            const status = await apiService.getDocumentStatus(response.document_id);
            
            if (status.status === 'completed') {
              setUploads(prev => prev.map(upload => 
                upload.id === uploadId 
                  ? { ...upload, status: 'completed' as const, progress: 100 }
                  : upload
              ));
              toast.success(`${file.name} uploaded and processed successfully!`);
            } else if (status.status === 'error') {
              setUploads(prev => prev.map(upload => 
                upload.id === uploadId 
                  ? { ...upload, status: 'error' as const, error: status.error_message }
                  : upload
              ));
              toast.error(`Error processing ${file.name}: ${status.error_message}`);
            } else {
              // Still processing, poll again
              setTimeout(pollStatus, 2000);
            }
          } catch (error) {
            setUploads(prev => prev.map(upload => 
              upload.id === uploadId 
                ? { ...upload, status: 'error' as const, error: 'Failed to check status' }
                : upload
            ));
            toast.error(`Failed to check status for ${file.name}`);
          }
        };

        setTimeout(pollStatus, 1000);
      } catch (error) {
        setUploads(prev => prev.map(upload => 
          upload.id === uploadId 
            ? { ...upload, status: 'error' as const, error: 'Upload failed' }
            : upload
        ));
        toast.error(`Failed to upload ${file.name}`);
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeUpload = (id: string) => {
    setUploads(prev => prev.filter(upload => upload.id !== id));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>;
      case 'processing':
        return <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600"></div>;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploading':
        return 'text-blue-600';
      case 'processing':
        return 'text-yellow-600';
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Documents</h1>
        <p className="text-gray-600">
          Upload PDF documents to add them to your knowledge base. Files will be processed and indexed for searching.
        </p>
      </div>

      {/* Upload Area */}
      <div className="card">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          {isDragActive ? (
            <p className="text-lg text-primary-600">Drop the PDF files here...</p>
          ) : (
            <div>
              <p className="text-lg text-gray-900 mb-2">
                Drag & drop PDF files here, or click to select files
              </p>
              <p className="text-sm text-gray-600">
                Maximum file size: 50MB. Only PDF files are supported.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Progress */}
      {uploads.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Progress</h2>
          <div className="space-y-4">
            {uploads.map((upload) => (
              <div
                key={upload.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1">
                  {getStatusIcon(upload.status)}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{upload.filename}</p>
                    <p className={`text-xs ${getStatusColor(upload.status)}`}>
                      {upload.status.charAt(0).toUpperCase() + upload.status.slice(1)}
                      {upload.error && `: ${upload.error}`}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {upload.progress !== undefined && upload.status !== 'completed' && upload.status !== 'error' && (
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${upload.progress}%` }}
                      ></div>
                    </div>
                  )}
                  
                  <button
                    onClick={() => removeUpload(upload.id)}
                    className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-blue-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Upload</h3>
            <p className="text-sm text-gray-600">
              Select or drag PDF files to upload them to the system
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-yellow-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-yellow-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Process</h3>
            <p className="text-sm text-gray-600">
              Documents are automatically processed and chunked for optimal retrieval
            </p>
          </div>
          
          <div className="text-center">
            <div className="bg-green-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
              <span className="text-green-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Search</h3>
            <p className="text-sm text-gray-600">
              Start asking questions about your uploaded documents
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload; 