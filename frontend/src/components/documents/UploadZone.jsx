import React, { useCallback, useEffect, useRef, useState } from 'react';
import { UploadCloud, FileText } from 'lucide-react';

export const UploadZone = ({ onFileSelect, disabled = false, error = null, success = null }) => {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = useCallback(
    (event) => {
      event.preventDefault();
      setDragActive(false);
      if (disabled) return;
      const file = event.dataTransfer.files?.[0];
      if (file) {
        onFileSelect(file);
      }
    },
    [disabled, onFileSelect]
  );

  const handleInput = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
    event.target.value = '';
  };

  useEffect(() => {
    const preventDefault = (event) => event.preventDefault();
    window.addEventListener('dragover', preventDefault);
    window.addEventListener('drop', preventDefault);
    return () => {
      window.removeEventListener('dragover', preventDefault);
      window.removeEventListener('drop', preventDefault);
    };
  }, []);

  return (
    <div
      className={`upload-zone ${dragActive ? 'drag-active' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={disabled ? -1 : 0}
      onKeyDown={(event) => {
        if (!disabled && (event.key === 'Enter' || event.key === ' ')) {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      aria-label="Upload document area. Drag and drop or press enter to choose a file."
      aria-disabled={disabled}
    >
      <input
        ref={inputRef}
        type="file"
        className="visually-hidden"
        onChange={handleInput}
        accept=".pdf,.docx,.txt,.md"
        disabled={disabled}
      />
      <div className="upload-zone-icon">
        <UploadCloud size={36} />
      </div>
      <div className="upload-zone-text">
        <h3>Drag and drop your document here</h3>
        <p>or click to browse from your computer</p>
      </div>
      <div className="upload-zone-meta">
        <FileText size={14} />
        <span>Supported formats: PDF, DOCX, TXT, MD (Max 25 MB)</span>
      </div>

      {error && (
        <div className="alert-message error" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="alert-message success" role="status">
          {success}
        </div>
      )}
    </div>
  );
};
