import React from 'react';
import { FiX, FiFile, FiImage, FiFileText } from 'react-icons/fi';

interface FilePreviewProps {
  file: File;
  onClose: () => void;
}

const getFileIcon = (type: string) => {
  if (type.startsWith('image/')) return <FiImage className="w-12 h-12 text-blue-500" />;
  if (type.includes('pdf') || type.includes('text')) return <FiFileText className="w-12 h-12 text-red-500" />;
  return <FiFile className="w-12 h-12 text-gray-500" />;
};

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const FilePreview: React.FC<FilePreviewProps> = ({ file, onClose }) => {
  const isImage = file.type.startsWith('image/');
  const objectUrl = isImage ? URL.createObjectURL(file) : null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900 truncate">{file.name}</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <FiX className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Preview */}
        <div className="flex-1 overflow-auto p-4 flex items-center justify-center">
          {isImage && objectUrl ? (
            <img
              src={objectUrl}
              alt={file.name}
              className="max-w-full max-h-[50vh] object-contain rounded"
              onLoad={() => URL.revokeObjectURL(objectUrl)}
            />
          ) : (
            <div className="text-center">
              {getFileIcon(file.type)}
              <p className="mt-2 text-sm text-gray-500">Preview not available</p>
            </div>
          )}
        </div>

        {/* File info */}
        <div className="px-4 py-3 border-t border-gray-200 text-sm text-gray-500">
          <div className="flex justify-between">
            <span>Size: {formatSize(file.size)}</span>
            <span>Type: {file.type || 'Unknown'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
