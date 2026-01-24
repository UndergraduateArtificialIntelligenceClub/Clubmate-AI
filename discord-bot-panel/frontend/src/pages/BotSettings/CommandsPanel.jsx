import React, { useState } from 'react';
import {
    Search, Plus, Edit2, Trash2, Grid, List,
    Users, Shield, Crown, ToggleLeft, ToggleRight
} from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { Badge } from '../../components/global/Badge';
import { Select } from '../../components/global/Select';
import { Modal } from '../../components/global/Modal';
import { Button } from '../../components/global/Button';
import { useToast } from '../../components/global/ToastContext';

const permissionOptions = [
    { value: 'everyone', label: 'Everyone', icon: Users },
    { value: 'moderator', label: 'Moderator', icon: Shield },
    { value: 'admin', label: 'Admin', icon: Crown },
];

const PermissionBadge = ({ permission }) => {
    const variants = {
        everyone: 'info',
        moderator: 'warning',
        admin: 'error',
    };
    const labels = {
        everyone: 'Everyone',
        moderator: 'Mod',
        admin: 'Admin',
    };
    return <Badge variant={variants[permission]}>{labels[permission]}</Badge>;
};

const CommandCard = ({ command, onEdit, onDelete, onToggle }) => (
    <div className="command-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div>
                <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 600 }}>{command.name}</h4>
                <code className="command-trigger" style={{ marginTop: '6px', display: 'inline-block' }}>
                    {command.trigger}
                </code>
            </div>
            <PermissionBadge permission={command.permission} />
        </div>
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {command.description}
        </p>
        {command.parameters?.length > 0 && (
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {command.parameters.map((param, idx) => (
                    <span
                        key={idx}
                        style={{
                            fontSize: '11px',
                            padding: '4px 8px',
                            background: 'var(--glass-bg)',
                            borderRadius: '6px',
                            color: param.endsWith('?') ? 'var(--text-secondary)' : 'var(--text-main)',
                        }}
                    >
                        {param}
                    </span>
                ))}
            </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
                <button
                    onClick={onEdit}
                    style={{
                        background: 'none',
                        border: 'none',
                        padding: '8px',
                        cursor: 'pointer',
                        color: 'var(--text-secondary)',
                        borderRadius: '8px',
                    }}
                >
                    <Edit2 size={16} />
                </button>
                <button
                    onClick={onDelete}
                    style={{
                        background: 'none',
                        border: 'none',
                        padding: '8px',
                        cursor: 'pointer',
                        color: 'var(--danger)',
                        borderRadius: '8px',
                    }}
                >
                    <Trash2 size={16} />
                </button>
            </div>
            <button
                onClick={onToggle}
                style={{
                    background: 'none',
                    border: 'none',
                    padding: '8px',
                    cursor: 'pointer',
                    color: command.enabled ? 'var(--status-online)' : 'var(--text-secondary)',
                }}
            >
                {command.enabled ? <ToggleRight size={24} /> : <ToggleLeft size={24} />}
            </button>
        </div>
    </div>
);

export default function CommandsPanel() {
    const { botConfig, updateCommand, addCommand, deleteCommand } = useBot();
    const { addToast } = useToast();
    const [viewMode, setViewMode] = useState('card');
    const [searchQuery, setSearchQuery] = useState('');
    const [filterPermission, setFilterPermission] = useState('all');
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingCommand, setEditingCommand] = useState(null);

    const [formData, setFormData] = useState({
        name: '',
        trigger: '',
        description: '',
        parameters: '',
        permission: 'everyone',
    });

    const filteredCommands = botConfig.commands.filter(cmd => {
        const matchesSearch = cmd.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            cmd.trigger.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesPermission = filterPermission === 'all' || cmd.permission === filterPermission;
        return matchesSearch && matchesPermission;
    });

    const handleOpenModal = (command = null) => {
        if (command) {
            setEditingCommand(command);
            setFormData({
                name: command.name,
                trigger: command.trigger,
                description: command.description,
                parameters: command.parameters?.join(', ') || '',
                permission: command.permission,
            });
        } else {
            setEditingCommand(null);
            setFormData({
                name: '',
                trigger: botConfig.invocation.prefix,
                description: '',
                parameters: '',
                permission: 'everyone',
            });
        }
        setIsModalOpen(true);
    };

    const handleSaveCommand = () => {
        const commandData = {
            name: formData.name,
            trigger: formData.trigger,
            description: formData.description,
            parameters: formData.parameters.split(',').map(p => p.trim()).filter(Boolean),
            permission: formData.permission,
            enabled: editingCommand?.enabled ?? true,
        };

        if (editingCommand) {
            updateCommand(editingCommand.id, commandData);
            addToast('Command updated successfully', 'success');
        } else {
            addCommand(commandData);
            addToast('Command added successfully', 'success');
        }
        setIsModalOpen(false);
    };

    const handleDeleteCommand = (id) => {
        if (window.confirm('Are you sure you want to delete this command?')) {
            deleteCommand(id);
            addToast('Command deleted', 'success');
        }
    };

    return (
        <div>
            {/* Toolbar */}
            <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '200px' }}>
                    <div style={{ position: 'relative' }}>
                        <Search
                            size={18}
                            style={{
                                position: 'absolute',
                                left: '14px',
                                top: '50%',
                                transform: 'translateY(-50%)',
                                color: 'var(--text-secondary)'
                            }}
                        />
                        <input
                            type="text"
                            className="form-input"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search commands..."
                            style={{ paddingLeft: '42px', width: '100%' }}
                        />
                    </div>
                </div>

                <Select
                    value={filterPermission}
                    onChange={setFilterPermission}
                    options={[
                        { value: 'all', label: 'All Permissions' },
                        ...permissionOptions,
                    ]}
                />

                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        className={`neu-outset`}
                        onClick={() => setViewMode('card')}
                        style={{
                            padding: '12px',
                            borderRadius: '12px',
                            border: 'none',
                            cursor: 'pointer',
                            color: viewMode === 'card' ? 'var(--accent)' : 'var(--text-secondary)',
                            boxShadow: viewMode === 'card'
                                ? 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)'
                                : undefined,
                        }}
                    >
                        <Grid size={18} />
                    </button>
                    <button
                        className={`neu-outset`}
                        onClick={() => setViewMode('table')}
                        style={{
                            padding: '12px',
                            borderRadius: '12px',
                            border: 'none',
                            cursor: 'pointer',
                            color: viewMode === 'table' ? 'var(--accent)' : 'var(--text-secondary)',
                            boxShadow: viewMode === 'table'
                                ? 'inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)'
                                : undefined,
                        }}
                    >
                        <List size={18} />
                    </button>
                </div>

                <Button onClick={() => handleOpenModal()}>
                    <Plus size={18} /> Add Command
                </Button>
            </div>

            {/* Commands Grid/Table */}
            {viewMode === 'card' ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {filteredCommands.map(cmd => (
                        <CommandCard
                            key={cmd.id}
                            command={cmd}
                            onEdit={() => handleOpenModal(cmd)}
                            onDelete={() => handleDeleteCommand(cmd.id)}
                            onToggle={() => updateCommand(cmd.id, { enabled: !cmd.enabled })}
                        />
                    ))}
                </div>
            ) : (
                <div className="neu-inset" style={{ borderRadius: '16px', overflow: 'hidden' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Command</th>
                                <th>Trigger</th>
                                <th>Permission</th>
                                <th>Status</th>
                                <th style={{ width: '100px' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredCommands.map(cmd => (
                                <tr key={cmd.id}>
                                    <td>
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{cmd.name}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{cmd.description}</div>
                                        </div>
                                    </td>
                                    <td><code className="command-trigger">{cmd.trigger}</code></td>
                                    <td><PermissionBadge permission={cmd.permission} /></td>
                                    <td>
                                        <Badge variant={cmd.enabled ? 'success' : 'neutral'}>
                                            {cmd.enabled ? 'Enabled' : 'Disabled'}
                                        </Badge>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button
                                                onClick={() => handleOpenModal(cmd)}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
                                            >
                                                <Edit2 size={16} />
                                            </button>
                                            <button
                                                onClick={() => updateCommand(cmd.id, { enabled: !cmd.enabled })}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: cmd.enabled ? 'var(--status-online)' : 'var(--text-secondary)' }}
                                            >
                                                {cmd.enabled ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
                                            </button>
                                            <button
                                                onClick={() => handleDeleteCommand(cmd.id)}
                                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--danger)' }}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {filteredCommands.length === 0 && (
                <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
                    <p>No commands found</p>
                </div>
            )}

            {/* Add/Edit Command Modal */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title={editingCommand ? 'Edit Command' : 'Add New Command'}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div className="form-group">
                        <label className="form-label">Command Name</label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            placeholder="e.g., help"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Trigger</label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.trigger}
                            onChange={(e) => setFormData({ ...formData, trigger: e.target.value })}
                            placeholder="e.g., !help"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Description</label>
                        <textarea
                            className="form-input form-textarea"
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="What does this command do?"
                            rows={3}
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Parameters (comma separated)</label>
                        <input
                            type="text"
                            className="form-input"
                            value={formData.parameters}
                            onChange={(e) => setFormData({ ...formData, parameters: e.target.value })}
                            placeholder="@user, reason?, duration?"
                        />
                        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                            Use ? suffix for optional parameters
                        </span>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Permission Level</label>
                        <Select
                            value={formData.permission}
                            onChange={(value) => setFormData({ ...formData, permission: value })}
                            options={permissionOptions}
                        />
                    </div>
                    <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '8px' }}>
                        <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                        <Button onClick={handleSaveCommand}>
                            {editingCommand ? 'Save Changes' : 'Add Command'}
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
