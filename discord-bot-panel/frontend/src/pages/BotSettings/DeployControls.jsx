import React from 'react';
import { Save, Upload, RefreshCw, Check, AlertCircle, Clock } from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { useToast } from '../../components/global/ToastContext';
import { Button } from '../../components/global/Button';
import { Badge } from '../../components/global/Badge';

export default function DeployControls() {
    const { botConfig, isSaving, saveDraft, deployToDiscord } = useBot();
    const { addToast } = useToast();

    const handleSaveDraft = async () => {
        const result = await saveDraft();
        if (result.success) {
            addToast('Draft saved successfully', 'success');
        } else {
            addToast('Failed to save draft', 'error');
        }
    };

    const handleDeploy = async () => {
        const result = await deployToDiscord();
        if (result.success) {
            addToast('Bot deployed to Discord!', 'success');
        } else {
            addToast('Deployment failed', 'error');
        }
    };

    const getStatusBadge = () => {
        switch (botConfig.syncStatus) {
            case 'synced':
                return <Badge variant="success"><Check size={12} /> Synced</Badge>;
            case 'pending':
                return <Badge variant="warning"><Clock size={12} /> Pending Changes</Badge>;
            case 'error':
                return <Badge variant="error"><AlertCircle size={12} /> Sync Error</Badge>;
            default:
                return null;
        }
    };

    const formatLastSynced = () => {
        if (!botConfig.lastSynced) return 'Never';
        const date = new Date(botConfig.lastSynced);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="deploy-bar">
            <div className="deploy-status">
                {getStatusBadge()}
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    Last synced: {formatLastSynced()}
                </span>
                {botConfig.hasUnsavedChanges && (
                    <span style={{ fontSize: '12px', color: 'var(--status-idle)', fontStyle: 'italic' }}>
                        • Unsaved changes
                    </span>
                )}
            </div>

            <div className="deploy-actions">
                <Button
                    variant="ghost"
                    onClick={handleSaveDraft}
                    disabled={isSaving || !botConfig.hasUnsavedChanges}
                >
                    {isSaving ? <RefreshCw size={18} className="animate-spin" /> : <Save size={18} />}
                    Save Draft
                </Button>
                <Button
                    onClick={handleDeploy}
                    disabled={isSaving}
                    style={{
                        background: 'linear-gradient(135deg, var(--discord-blurple), var(--accent))',
                        color: 'white',
                    }}
                >
                    {isSaving ? <RefreshCw size={18} className="animate-spin" /> : <Upload size={18} />}
                    Deploy to Discord
                </Button>
            </div>
        </div>
    );
}
