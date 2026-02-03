import React, { useState, useCallback, useRef } from 'react';

/**
 * DocumentUpload - Drag-and-drop file upload with document classification
 * 
 * Features:
 * - Drag and drop support
 * - File type validation
 * - Progress indication
 * - Document classification preview
 * - Batch upload support
 */

const ACCEPTED_TYPES = {
  'application/pdf': '.pdf',
  'application/msword': '.doc',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/vnd.ms-excel': '.xls',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
  'text/plain': '.txt',
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'model/ifc': '.ifc',
};

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

const DocumentTypeIcon = ({ type }) => {
  const icons = {
    Contract: '📄',
    Drawing: '📐',
    RFI: '❓',
    Submittal: '📋',
    'Change Order': '🔄',
    'Meeting Minutes': '📝',
    Invoice: '💰',
    Schedule: '📅',
    Report: '📊',
    Specification: '📑',
    default: '📎',
  };
  return <span className="text-2xl">{icons[type] || icons.default}</span>;
};

const FileCard = ({ file, classification, onRemove, isUploading }) => {
  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-100">
        {classification ? (
          <DocumentTypeIcon type={classification.document_type} />
        ) : (
          <span className="text-2xl">📄</span>
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="truncate font-medium text-gray-900">{file.name}</p>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>{formatSize(file.size)}</span>
          {classification && (
            <>
              <span>•</span>
              <span className="text-[#a67c52] font-medium">
                {classification.document_type}
              </span>
              <span className="text-xs bg-gray-100 px-2 py-0.5 rounded-full">
                {Math.round(classification.confidence * 100)}% confident
              </span>
            </>
          )}
        </div>
      </div>

      {isUploading ? (
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-[#a67c52]" />
      ) : (
        <button
          onClick={onRemove}
          className="rounded-full p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default function DocumentUpload({ projectId, onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [classifications, setClassifications] = useState({});
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const validateFile = (file) => {
    if (file.size > MAX_FILE_SIZE) {
      return `File "${file.name}" exceeds 50MB limit`;
    }
    // Allow all files for now, classification will handle types
    return null;
  };

  const classifyFile = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/classify/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        return result;
      }
    } catch (err) {
      console.error('Classification failed:', err);
    }
    return null;
  };

  const handleFiles = useCallback(async (newFiles) => {
    setError(null);
    const validFiles = [];
    
    for (const file of newFiles) {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    setFiles(prev => [...prev, ...validFiles]);

    // Classify each file
    for (const file of validFiles) {
      const classification = await classifyFile(file);
      if (classification) {
        setClassifications(prev => ({
          ...prev,
          [file.name]: classification,
        }));
      }
    }
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  }, [handleFiles]);

  const handleFileSelect = useCallback((e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFiles(selectedFiles);
    e.target.value = ''; // Reset input
  }, [handleFiles]);

  const removeFile = useCallback((fileName) => {
    setFiles(prev => prev.filter(f => f.name !== fileName));
    setClassifications(prev => {
      const updated = { ...prev };
      delete updated[fileName];
      return updated;
    });
  }, []);

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const totalFiles = files.length;
      let uploaded = 0;

      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        if (projectId) {
          formData.append('project_id', projectId);
        }

        const classification = classifications[file.name];
        if (classification) {
          formData.append('document_type', classification.document_type);
        }

        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed to upload ${file.name}`);
        }

        uploaded++;
        setUploadProgress(Math.round((uploaded / totalFiles) * 100));
      }

      // Clear files after successful upload
      setFiles([]);
      setClassifications({});
      
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${isDragging 
            ? 'border-[#a67c52] bg-[#f6efe6]' 
            : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.ifc"
        />

        <div className="flex flex-col items-center gap-3">
          <div className={`rounded-full p-4 ${isDragging ? 'bg-[#a67c52]/10' : 'bg-gray-200'}`}>
            <svg className={`h-8 w-8 ${isDragging ? 'text-[#a67c52]' : 'text-gray-500'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>

          <div>
            <p className="text-lg font-medium text-gray-700">
              {isDragging ? 'Drop files here' : 'Drag & drop files'}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              or click to browse • PDF, Word, Excel, Images, IFC
            </p>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </h3>
            <button
              onClick={() => {
                setFiles([]);
                setClassifications({});
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Clear all
            </button>
          </div>

          <div className="space-y-2">
            {files.map((file) => (
              <FileCard
                key={file.name}
                file={file}
                classification={classifications[file.name]}
                onRemove={() => removeFile(file.name)}
                isUploading={isUploading}
              />
            ))}
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="space-y-2">
              <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                <div 
                  className="h-full bg-[#a67c52] transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-center text-sm text-gray-500">
                Uploading... {uploadProgress}%
              </p>
            </div>
          )}

          {/* Upload Button */}
          {!isUploading && (
            <button
              onClick={uploadFiles}
              className="w-full rounded-lg bg-[#a67c52] py-3 font-semibold text-white shadow-sm transition-all hover:bg-[#8b6844] focus:outline-none focus:ring-2 focus:ring-[#a67c52] focus:ring-offset-2"
            >
              Upload {files.length} File{files.length !== 1 ? 's' : ''}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
