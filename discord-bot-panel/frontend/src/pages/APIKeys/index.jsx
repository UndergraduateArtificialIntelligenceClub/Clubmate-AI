import React, { useState, useEffect } from 'react';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { Input } from '../../components/global/Input';
import { Button } from '../../components/global/Button';
import { Copy, Plus } from 'lucide-react';
import { useToast } from '../../components/global/ToastContext';
import api from '../../services/api';

export default function APIKeys() {
  const [keys, setKeys] = useState([]);
  const [form, setForm] = useState({ name: '', value: '' });
  const [loading, setLoading] = useState(false);
  const { addToast } = useToast();

  const fetchKeys = async () => {
    try {
      const res = await api.getKeys();
      setKeys(res.data);
    } catch (err) {
      addToast("Failed to load API keys", "error");
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleAdd = async () => {
    if (!form.name || !form.value) return addToast("Please fill in all fields", "info");
    setLoading(true);
    try {
      await api.createKey(form);
      setForm({ name: '', value: '' });
      addToast("API Key added securely", "success");
      fetchKeys();
    } catch (err) {
      addToast("Failed to add key", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (id) => {
    if (!window.confirm("Revoke this API key? This cannot be undone.")) return;
    try {
      await api.revokeKey(id);
      setKeys(prev => prev.filter(k => k.id !== id));
      addToast("API Key revoked", "info");
    } catch (err) {
      addToast("Failed to revoke key", "error");
    }
  };

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <NeomorphicCard>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <Input 
              label="Service Name" 
              placeholder="e.g. OpenAI" 
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
            />
          </div>
          <div style={{ flex: 2 }}>
            <Input 
              label="API Secret Key" 
              placeholder="Paste your key here..." 
              type="password"
              value={form.value}
              onChange={e => setForm({...form, value: e.target.value})}
            />
          </div>
          <div style={{ marginBottom: '16px' }}>
            <Button onClick={handleAdd} disabled={loading}>
              <Plus size={18} /> {loading ? 'Adding...' : 'Add Key'}
            </Button>
          </div>
        </div>
      </NeomorphicCard>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        {keys.map(key => (
          <NeomorphicCard key={key.id} title={key.name}>
            <div className="neu-inset" style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
              {key.masked}
              <Button style={{ padding: '4px', height: '28px' }}>
                <Copy size={14}/>
              </Button>
            </div>
            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                Added: {new Date(key.created_at).toLocaleDateString()}
              </span>
              <Button 
                variant="danger" 
                style={{ fontSize: '12px', padding: '6px 12px' }}
                onClick={() => handleRevoke(key.id)}
              >
                Revoke
              </Button>
            </div>
          </NeomorphicCard>
        ))}
      </div>
    </div>
  );
}
