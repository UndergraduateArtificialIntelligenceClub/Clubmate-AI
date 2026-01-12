import React, { useState, useEffect } from 'react';
import { NeomorphicCard } from '../../components/global/NeomorphicCard';
import { Search, Plus, Trash2, User, Shield, Ban } from 'lucide-react';
import { Modal } from '../../components/global/Modal';
import { Input } from '../../components/global/Input';
import { Button } from '../../components/global/Button';
import { useToast } from '../../components/global/ToastContext';
import api from '../../services/api';

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { addToast } = useToast();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    discord_id: '',
    discord_username: '',
    notes: '',
    tags: ''
  });

  const fetchContacts = async () => {
    try {
      const res = await api.getContacts();
      setContacts(res.data);
    } catch (err) {
      addToast("Failed to load contacts", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  const handleCreate = async () => {
    try {
      const payload = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
      };
      await api.createContact(payload);
      setIsModalOpen(false);
      setFormData({ name: '', email: '', phone: '', discord_id: '', discord_username: '', notes: '', tags: '' });
      addToast("Contact created successfully", "success");
      fetchContacts();
    } catch (err) {
      addToast(err.response?.data?.detail || "Failed to create contact", "error");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await api.deleteContact(id);
      setContacts(prev => prev.filter(c => c.id !== id));
      addToast("Contact deleted", "info");
    } catch (err) {
      addToast("Failed to delete contact", "error");
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div className="neu-inset" style={{
          display: 'flex', alignItems: 'center', padding: '12px',
          background: 'var(--bg-color)', width: '400px'
        }}>
          <Search size={20} style={{ color: 'var(--text-secondary)', marginRight: '12px' }} />
          <input
            type="text"
            placeholder="Search by username or ID..."
            style={{
              border: 'none', background: 'transparent', outline: 'none',
              width: '100%', color: 'var(--text-main)', fontSize: '16px'
            }}
          />
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={18} /> Add Contact
        </Button>
      </div>

      <NeomorphicCard>
        {loading ? (
          <div style={{ padding: '20px', textAlign: 'center' }}>Loading...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: 'var(--text-secondary)', fontSize: '14px', borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                <th style={{ padding: '12px' }}>Name</th>
                <th style={{ padding: '12px' }}>Email</th>
                <th style={{ padding: '12px' }}>Phone</th>
                <th style={{ padding: '12px' }}>Discord</th>
                <th style={{ padding: '12px' }}>Tags</th>
                <th style={{ padding: '12px' }}></th>
              </tr>
            </thead>
            <tbody>
              {contacts.map(contact => (
                <tr key={contact.id} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                  <td style={{ padding: '16px 12px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div className="neu-outset" style={{ width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <User size={16} color="var(--accent)" />
                    </div>
                    {contact.name}
                  </td>
                  <td style={{ padding: '16px 12px', color: 'var(--text-secondary)' }}>
                    {contact.email || '-'}
                  </td>
                  <td style={{ padding: '16px 12px', color: 'var(--text-secondary)' }}>
                    {contact.phone || '-'}
                  </td>
                  <td style={{ padding: '16px 12px', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
                    {contact.discord_username || contact.discord_id || '-'}
                  </td>
                  <td style={{ padding: '16px 12px' }}>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {contact.tags && contact.tags.length > 0 ? contact.tags.map((tag, idx) => (
                        <span key={idx} style={{
                          background: 'rgba(109, 93, 252, 0.1)', color: 'var(--accent)',
                          padding: '4px 8px', borderRadius: '8px', fontSize: '11px', fontWeight: 'bold'
                        }}>
                          {tag}
                        </span>
                      )) : <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No tags</span>}
                    </div>
                  </td>
                  <td style={{ padding: '16px 12px', textAlign: 'right' }}>
                    <button
                      onClick={() => handleDelete(contact.id)}
                      className="neu-btn"
                      style={{ padding: '8px', color: 'var(--danger)' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </NeomorphicCard>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Add New Contact">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Full Name"
          />
          <Input
            label="Email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="email@example.com"
          />
          <Input
            label="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            placeholder="+1-555-123-4567"
          />
          <Input
            label="Discord Username"
            value={formData.discord_username}
            onChange={(e) => setFormData({ ...formData, discord_username: e.target.value })}
            placeholder="username#1234"
          />
          <Input
            label="Tags (comma separated)"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            placeholder="member, sponsor, volunteer"
          />
          <Button onClick={handleCreate} style={{ marginTop: '16px', width: '100%', justifyContent: 'center' }}>
            Create Contact
          </Button>
        </div>
      </Modal>
    </div>
  );
}
