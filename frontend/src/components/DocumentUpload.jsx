import { useRef, useState } from 'react';
import { getSyncStatus, getUploadUrl, syncKnowledgeBase } from '../api/bedrockApi';
import './DocumentUpload.css';

const MAX_FILE_SIZE = 50 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ['pdf', 'txt', 'html', 'docx', 'csv', 'md'];
const COMPLETE_STATUSES = ['COMPLETE', 'COMPLETED'];
const FAILED_STATUSES = ['FAILED', 'STOPPED'];

function getFileExtension(fileName) {
  return fileName.split('.').pop()?.toLowerCase() || '';
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function uploadToS3(file, uploadUrl, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = event => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100);
        resolve();
      } else {
        reject(new Error(`S3 upload failed with HTTP ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error('S3 upload failed. Check bucket CORS settings.'));
    xhr.open('PUT', uploadUrl);
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
    xhr.send(file);
  });
}

export default function DocumentUpload() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [stage, setStage] = useState('idle');
  const [statusText, setStatusText] = useState('Choose a document to add to the knowledge base.');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  function validateFile(nextFile) {
    const extension = getFileExtension(nextFile.name);

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return `Unsupported file type. Use ${ALLOWED_EXTENSIONS.join(', ')}.`;
    }

    if (nextFile.size > MAX_FILE_SIZE) {
      return 'File is too large. Maximum size is 50MB.';
    }

    return '';
  }

  function selectFile(nextFile) {
    if (!nextFile || isUploading) return;

    const validationError = validateFile(nextFile);
    setError(validationError);
    setResult(null);
    setUploadProgress(0);
    setStage(validationError ? 'idle' : 'selected');
    setStatusText(validationError || 'Ready to upload and sync.');
    setFile(validationError ? null : nextFile);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  async function pollSyncStatus(jobId) {
    for (let attempt = 0; attempt < 80; attempt += 1) {
      const data = await getSyncStatus(jobId);

      if (COMPLETE_STATUSES.includes(data.status)) {
        return data;
      }

      if (FAILED_STATUSES.includes(data.status)) {
        const reason = data.failureReasons?.[0] || 'Knowledge base sync failed.';
        throw new Error(reason);
      }

      setStatusText(`Sync status: ${data.status}`);
      await wait(3000);
    }

    throw new Error('Sync is still running. Check the Bedrock console for final status.');
  }

  async function handleUpload() {
    if (!file || isUploading) return;

    setIsUploading(true);
    setError('');
    setResult(null);

    try {
      setStage('uploading');
      setStatusText('Creating secure upload URL...');
      const uploadData = await getUploadUrl(file);

      setStatusText('Uploading document to S3...');
      await uploadToS3(file, uploadData.uploadUrl, setUploadProgress);

      setStage('syncing');
      setStatusText('Starting knowledge base sync...');
      const syncData = await syncKnowledgeBase();

      setStatusText(`Sync status: ${syncData.status}`);
      const finalStatus = await pollSyncStatus(syncData.jobId);

      setStage('complete');
      setStatusText('Document is ready in the knowledge base.');
      setResult({
        s3Key: uploadData.s3Key,
        jobId: finalStatus.jobId,
      });
    } catch (err) {
      setStage('error');
      setError(err.message);
      setStatusText('Upload failed.');
    } finally {
      setIsUploading(false);
    }
  }

  const steps = [
    { id: 'selected', label: 'File' },
    { id: 'uploading', label: 'S3' },
    { id: 'syncing', label: 'Sync' },
    { id: 'complete', label: 'Ready' },
  ];
  const activeStep = Math.max(steps.findIndex(step => step.id === stage), stage === 'error' ? 0 : -1);

  return (
    <div className="document-upload">
      <button
        type="button"
        className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        disabled={isUploading}
      >
        <span className="upload-icon">+</span>
        <span className="upload-title">{file ? file.name : 'Upload document'}</span>
        <span className="upload-subtitle">PDF, TXT, HTML, DOCX, CSV, MD</span>
      </button>

      <input
        ref={inputRef}
        type="file"
        className="upload-input"
        accept=".pdf,.txt,.html,.htm,.docx,.csv,.md"
        onChange={(event) => selectFile(event.target.files?.[0])}
      />

      <div className="upload-pipeline" aria-label="Upload progress">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`pipeline-step ${index <= activeStep ? 'active' : ''} ${stage === step.id ? 'current' : ''}`}
          >
            <span className="pipeline-dot"></span>
            <span className="pipeline-label">{step.label}</span>
          </div>
        ))}
      </div>

      <div className="upload-progress-track">
        <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }}></div>
      </div>

      <p className={`upload-status ${error ? 'error' : ''}`}>{error || statusText}</p>

      {result && (
        <div className="upload-result">
          <span>S3 key: {result.s3Key}</span>
          <span>Job ID: {result.jobId}</span>
        </div>
      )}

      <button
        type="button"
        className="upload-action"
        onClick={handleUpload}
        disabled={!file || isUploading}
      >
        {isUploading ? 'Working...' : 'Upload & Sync'}
      </button>
    </div>
  );
}
