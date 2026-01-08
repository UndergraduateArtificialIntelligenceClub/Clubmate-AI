import React, { useState, useEffect, useRef } from 'react';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { FileText, Upload, Trash2, Download } from 'lucide-react';
import { useToast } from '../../components/global/ToastContext';
import api from '../../services/api';

export default function Files() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);
  const { addToast } = useToast();

  const fetchFiles = async () => {
    try {
      const res = await api.getFiles();
      setFiles(res.data);
    } catch (err) {
      addToast("Failed to load files", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleUploadClick = () => fileInputRef.current.click();

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      await api.uploadFile(formData);
      addToast("File uploaded successfully", "success");
      await fetchFiles();
    } catch (err) {
      addToast("Upload failed", "error");
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this file permanently?")) return;
    try {
      await api.deleteFile(id);
      setFiles(prev => prev.filter(f => f.id !== id));
      addToast("File deleted", "info");
    } catch (err) {
      addToast("Failed to delete file", "error");
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
        <button onClick={handleUploadClick} className="neu-outset neu-btn">
          <Upload size={18} /> Upload File
        </button>
      </div>

      {loading && files.length === 0 ? (
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Loading files...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '20px' }}>
          {files.map(file => (
            <NeomorphicCard key={file.id} style={{ padding: '16px', textAlign: 'center' }}>
              <div style={{ marginBottom: '12px', color: 'var(--accent)' }}>
                <FileText size={40} />
              </div>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={file.filename}>
                {file.filename}
              </h4>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                {formatSize(file.file_size_bytes)} • {new Date(file.created_at).toLocaleDateString()}
              </p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                <button className="neu-outset neu-btn" style={{ padding: '8px' }}>
                  <Download size={14} />
                </button>
                <button 
                  onClick={() => handleDelete(file.id)}
                  className="neu-outset neu-btn" 
                  style={{ padding: '8px', color: 'var(--danger)' }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </NeomorphicCard>
          ))}
        </div>
      )}
    </div>
  );
}
