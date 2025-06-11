import React, { useCallback, useState } from 'react';
import { Patient } from '../types/patient.types';

interface FileUploaderProps {
  onLoad: (patients: Patient[]) => void;
  isLoading?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onLoad, isLoading = false }) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (!file.name.endsWith('.json')) {
      setError('Please select a JSON file');
      return;
    }

    try {
      setError(null);
      const text = await file.text();
      const data = JSON.parse(text);

      // Validate that it's an array
      if (!Array.isArray(data)) {
        setError('File must contain an array of patients');
        return;
      }

      // Basic validation of patient structure
      const validPatients = data.filter((item: any) => {
        return (
          item &&
          typeof item.id === 'string' &&
          typeof item.nationality === 'string' &&
          ['T1', 'T2', 'T3'].includes(item.triage_category) &&
          ['KIA', 'RTD', 'Remains_Role4'].includes(item.final_status) &&
          Array.isArray(item.movement_timeline)
        );
      });

      if (validPatients.length === 0) {
        setError('No valid patients found in file');
        return;
      }

      if (validPatients.length !== data.length) {
        console.warn(`Warning: ${data.length - validPatients.length} invalid patients filtered out`);
      }

      onLoad(validPatients as Patient[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse JSON file');
    }
  }, [onLoad]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
  }, [handleFiles]);

  return (
    <div className="w-full max-w-md mx-auto p-6">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200
          ${dragActive 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isLoading ? 'opacity-50 pointer-events-none' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".json"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isLoading}
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <svg 
              className="w-12 h-12 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
              />
            </svg>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {isLoading ? 'Loading...' : 'Upload Patient Data'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop a patients.json file here, or click to browse
            </p>
          </div>

          <div className="text-xs text-gray-400 space-y-1">
            <p>Expected format: JSON array of patient objects</p>
            <p>Required fields: id, nationality, triage_category, final_status, movement_timeline</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
};