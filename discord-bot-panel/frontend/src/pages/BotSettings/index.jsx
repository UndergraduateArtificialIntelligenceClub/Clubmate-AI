import React, { useState } from 'react';
import {
    Bot, Hash, Terminal, Cpu, MessageSquare, Save,
    Upload, ChevronDown, ChevronUp, Zap, Shield
} from 'lucide-react';
import { useBot } from '../../context/BotContext';
import { useToast } from '../../components/global/ToastContext';
import BotIdentity from './BotIdentity';
import InvocationSettings from './InvocationSettings';
import CommandsPanel from './CommandsPanel';
import FeaturesPanel from './FeaturesPanel';
import PromptSettings from './PromptSettings';
import DeployControls from './DeployControls';

const CollapsibleSection = ({ title, icon: Icon, children, defaultOpen = true }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="section-card" style={{ marginBottom: '24px' }}>
            <div
                className="collapsible-header"
                onClick={() => setIsOpen(!isOpen)}
                style={{ margin: '-16px', marginBottom: isOpen ? '16px' : '-16px' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="neu-inset" style={{ padding: '10px', borderRadius: '12px', color: 'var(--accent)' }}>
                        <Icon size={20} />
                    </div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>{title}</h3>
                </div>
                {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </div>
            <div className={`collapsible-content ${isOpen ? 'expanded' : 'collapsed'}`}>
                {children}
            </div>
        </div>
    );
};

export default function BotSettings() {
    const { botConfig, isSaving } = useBot();
    const { addToast } = useToast();

    return (
        <div className="animate-fadeIn" style={{ paddingBottom: '100px' }}>
            {/* Page Header */}
            <div style={{ marginBottom: '32px' }}>
                <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 700 }}>Bot Settings</h1>
                <p style={{ margin: '8px 0 0', color: 'var(--text-secondary)' }}>
                    Configure your Discord bot's identity, commands, and behavior
                </p>
            </div>

            {/* Bot Identity Section */}
            <CollapsibleSection title="Bot Identity" icon={Bot}>
                <BotIdentity />
            </CollapsibleSection>

            {/* Invocation Settings Section */}
            <CollapsibleSection title="Invocation & Wake Mechanism" icon={Hash}>
                <InvocationSettings />
            </CollapsibleSection>

            {/* Commands Configuration Section */}
            <CollapsibleSection title="Commands Configuration" icon={Terminal}>
                <CommandsPanel />
            </CollapsibleSection>

            {/* Bot Features Section */}
            <CollapsibleSection title="Bot Features" icon={Cpu}>
                <FeaturesPanel />
            </CollapsibleSection>

            {/* Prompt & Personality Section */}
            <CollapsibleSection title="Prompt & Personality" icon={MessageSquare}>
                <PromptSettings />
            </CollapsibleSection>

            {/* Deploy Bar */}
            <DeployControls />
        </div>
    );
}
