import React, { createContext, useContext, useState, useCallback } from 'react';

const BotContext = createContext();

// Default bot configuration
const defaultBotConfig = {
    // Bot Identity
    identity: {
        name: 'ClubMate Bot',
        username: 'clubmate',
        avatarUrl: '',
        status: 'online', // online, idle, dnd, offline
        bio: 'Your friendly Discord assistant for managing club activities.',
    },

    // Invocation Settings
    invocation: {
        prefix: '!',
        mentionEnabled: true,
        customTag: '',
        mode: 'hybrid', // prefix, mention, hybrid
    },

    // Commands
    commands: [
        {
            id: '1',
            name: 'help',
            trigger: '!help',
            description: 'Display available commands and usage information',
            parameters: [],
            permission: 'everyone',
            enabled: true,
        },
        {
            id: '2',
            name: 'kick',
            trigger: '!kick',
            description: 'Kick a user from the server',
            parameters: ['@user', 'reason?'],
            permission: 'moderator',
            enabled: true,
        },
        {
            id: '3',
            name: 'ban',
            trigger: '!ban',
            description: 'Ban a user from the server',
            parameters: ['@user', 'duration?', 'reason?'],
            permission: 'admin',
            enabled: true,
        },
        {
            id: '4',
            name: 'mute',
            trigger: '!mute',
            description: 'Mute a user in voice/text channels',
            parameters: ['@user', 'duration', 'reason?'],
            permission: 'moderator',
            enabled: true,
        },
        {
            id: '5',
            name: 'ask',
            trigger: '!ask',
            description: 'Ask the AI a question and get a response',
            parameters: ['question'],
            permission: 'everyone',
            enabled: true,
        },
    ],

    // Features
    features: {
        aiChat: { enabled: true, model: 'gpt-4', maxTokens: 2048 },
        moderation: { enabled: true, autoMod: true, profanityFilter: true },
        autoReplies: { enabled: false, rules: [] },
        logging: { enabled: true, channel: 'bot-logs' },
        serverAnalytics: { enabled: false },
        welcomeMessages: { enabled: true, channel: 'welcome', message: 'Welcome to the server, {user}!' },
    },

    // Prompt/Personality
    prompt: {
        systemPrompt: 'You are ClubMate, a helpful and friendly Discord bot. You assist users with club activities, answer questions, and help maintain a positive community atmosphere.',
        personality: 'friendly', // friendly, professional, sarcastic, custom
        toneFormality: 50, // 0 = casual, 100 = formal
        responseLength: 50, // 0 = short, 100 = detailed
    },

    // Sync Status
    syncStatus: 'synced', // synced, pending, error
    lastSynced: new Date().toISOString(),
    hasUnsavedChanges: false,
};

export const BotProvider = ({ children }) => {
    const [botConfig, setBotConfig] = useState(defaultBotConfig);
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Update identity
    const updateIdentity = useCallback((updates) => {
        setBotConfig(prev => ({
            ...prev,
            identity: { ...prev.identity, ...updates },
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    // Update invocation settings
    const updateInvocation = useCallback((updates) => {
        setBotConfig(prev => ({
            ...prev,
            invocation: { ...prev.invocation, ...updates },
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    // Update commands
    const updateCommand = useCallback((commandId, updates) => {
        setBotConfig(prev => ({
            ...prev,
            commands: prev.commands.map(cmd =>
                cmd.id === commandId ? { ...cmd, ...updates } : cmd
            ),
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    const addCommand = useCallback((command) => {
        const newCommand = {
            ...command,
            id: Date.now().toString(),
        };
        setBotConfig(prev => ({
            ...prev,
            commands: [...prev.commands, newCommand],
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    const deleteCommand = useCallback((commandId) => {
        setBotConfig(prev => ({
            ...prev,
            commands: prev.commands.filter(cmd => cmd.id !== commandId),
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    // Update features
    const updateFeature = useCallback((featureName, updates) => {
        setBotConfig(prev => ({
            ...prev,
            features: {
                ...prev.features,
                [featureName]: { ...prev.features[featureName], ...updates },
            },
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    // Update prompt/personality
    const updatePrompt = useCallback((updates) => {
        setBotConfig(prev => ({
            ...prev,
            prompt: { ...prev.prompt, ...updates },
            hasUnsavedChanges: true,
            syncStatus: 'pending',
        }));
    }, []);

    // Save draft (mock)
    const saveDraft = useCallback(async () => {
        setIsSaving(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 800));
        setBotConfig(prev => ({
            ...prev,
            hasUnsavedChanges: false,
        }));
        setIsSaving(false);
        return { success: true };
    }, []);

    // Deploy to Discord (mock)
    const deployToDiscord = useCallback(async () => {
        setIsSaving(true);
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        setBotConfig(prev => ({
            ...prev,
            syncStatus: 'synced',
            lastSynced: new Date().toISOString(),
            hasUnsavedChanges: false,
        }));
        setIsSaving(false);
        return { success: true };
    }, []);

    // Reset to defaults
    const resetToDefaults = useCallback(() => {
        setBotConfig(defaultBotConfig);
    }, []);

    return (
        <BotContext.Provider value={{
            botConfig,
            isLoading,
            isSaving,
            updateIdentity,
            updateInvocation,
            updateCommand,
            addCommand,
            deleteCommand,
            updateFeature,
            updatePrompt,
            saveDraft,
            deployToDiscord,
            resetToDefaults,
        }}>
            {children}
        </BotContext.Provider>
    );
};

export const useBot = () => {
    const context = useContext(BotContext);
    if (!context) {
        throw new Error('useBot must be used within a BotProvider');
    }
    return context;
};

export default BotContext;
