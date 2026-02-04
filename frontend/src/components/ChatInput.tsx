import React, { useState, useRef, useCallback } from 'react';
import { FiSend, FiPaperclip, FiGlobe, FiX } from 'react-icons/fi';

interface ChatInputProps {
  onSendMessage: (content: string, files?: File[], useInternet?: boolean) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [useInternet, setUseInternet] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = message.trim();
    if (!trimmed && files.length === 0) return;

    onSendMessage(trimmed, files.length > 0 ? files : undefined, useInternet);
    setMessage('');
    setFiles([]);
  }, [message, files, useInternet, onSendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      {/* Attached files */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {files.map((file, i) => (
            <div
              key={i}
              className="flex items-center gap-1 bg-gray-100 rounded-lg px-2 py-1 text-xs text-gray-700"
            >
              <span className="max-w-[120px] truncate">{file.name}</span>
              <button onClick={() => removeFile(i)} className="hover:text-red-500">
                <FiX className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        {/* File upload */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
          title="Attach files"
        >
          <FiPaperclip className="w-5 h-5" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Internet toggle */}
        <button
          onClick={() => setUseInternet(!useInternet)}
          className={`p-2 rounded-lg transition-colors ${
            useInternet
              ? 'bg-primary-100 text-primary-700'
              : 'hover:bg-gray-100 text-gray-500'
          }`}
          title="Search the internet"
        >
          <FiGlobe className="w-5 h-5" />
        </button>

        {/* Message input */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none disabled:opacity-50 max-h-32"
          style={{ minHeight: '40px' }}
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={disabled || (!message.trim() && files.length === 0)}
          className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Send message"
        >
          <FiSend className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};
