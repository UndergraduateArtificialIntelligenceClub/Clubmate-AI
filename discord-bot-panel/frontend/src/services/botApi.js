// Bot API service for mock data and future API integration

// Mock request logs data
const mockRequestLogs = [
    {
        id: '1',
        timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
        serverName: 'Tech Community',
        serverId: '123456789',
        channelName: 'general',
        userName: 'JohnDoe',
        userId: '987654321',
        command: 'help',
        invocationType: 'prefix',
        prompt: '!help',
        featureTriggered: 'Commands',
        status: 'success',
        executionTime: 45,
        response: { message: 'Here are the available commands...' },
    },
    {
        id: '2',
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        serverName: 'Gaming Hub',
        serverId: '234567890',
        channelName: 'bot-commands',
        userName: 'GamerPro',
        userId: '876543210',
        command: 'ask',
        invocationType: 'mention',
        prompt: '@ClubMate What is the best gaming setup?',
        featureTriggered: 'AI Chat',
        status: 'success',
        executionTime: 1250,
        response: { message: 'The best gaming setup depends on your needs...' },
    },
    {
        id: '3',
        timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
        serverName: 'Study Group',
        serverId: '345678901',
        channelName: 'homework-help',
        userName: 'StudentA',
        userId: '765432109',
        command: 'ask',
        invocationType: 'prefix',
        prompt: '!ask Explain quantum computing in simple terms',
        featureTriggered: 'AI Chat',
        status: 'success',
        executionTime: 2100,
        response: { message: 'Quantum computing is a type of computation...' },
    },
    {
        id: '4',
        timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
        serverName: 'Tech Community',
        serverId: '123456789',
        channelName: 'moderation',
        userName: 'ModeratorX',
        userId: '654321098',
        command: 'kick',
        invocationType: 'prefix',
        prompt: '!kick @SpamBot Spamming links',
        featureTriggered: 'Moderation',
        status: 'success',
        executionTime: 120,
        response: { message: 'User SpamBot has been kicked.' },
    },
    {
        id: '5',
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        serverName: 'Art Club',
        serverId: '456789012',
        channelName: 'showcase',
        userName: 'Artist123',
        userId: '543210987',
        command: 'unknown',
        invocationType: 'prefix',
        prompt: '!unknowncommand',
        featureTriggered: 'Commands',
        status: 'error',
        executionTime: 15,
        error: 'Unknown command: unknowncommand',
    },
    {
        id: '6',
        timestamp: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
        serverName: 'Gaming Hub',
        serverId: '234567890',
        channelName: 'general',
        userName: 'NewUser',
        userId: '432109876',
        command: 'help',
        invocationType: 'slash',
        prompt: '/help',
        featureTriggered: 'Commands',
        status: 'success',
        executionTime: 38,
        response: { message: 'Here are the available commands...' },
    },
    {
        id: '7',
        timestamp: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
        serverName: 'Study Group',
        serverId: '345678901',
        channelName: 'bot-testing',
        userName: 'Tester',
        userId: '321098765',
        command: 'ask',
        invocationType: 'mention',
        prompt: '@ClubMate This is a very long request that might timeout',
        featureTriggered: 'AI Chat',
        status: 'timeout',
        executionTime: 30000,
        error: 'Request timed out after 30 seconds',
    },
    {
        id: '8',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        serverName: 'Tech Community',
        serverId: '123456789',
        channelName: 'announcements',
        userName: 'Admin',
        userId: '210987654',
        command: 'announce',
        invocationType: 'prefix',
        prompt: '!announce Server maintenance at 10 PM',
        featureTriggered: 'Admin',
        status: 'success',
        executionTime: 85,
        response: { message: 'Announcement sent to #announcements' },
    },
];

// Simulate API delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export const botApi = {
    // Get bot configuration
    async getBotConfig() {
        await delay(500);
        // Return from localStorage or default
        const stored = localStorage.getItem('botConfig');
        return stored ? JSON.parse(stored) : null;
    },

    // Save bot configuration
    async saveBotConfig(config) {
        await delay(800);
        localStorage.setItem('botConfig', JSON.stringify(config));
        return { success: true };
    },

    // Deploy to Discord
    async deployBot(config) {
        await delay(1500);
        // Simulate deployment
        return { success: true, deployedAt: new Date().toISOString() };
    },

    // Get request logs
    async getRequestLogs({ page = 1, limit = 20, filters = {} } = {}) {
        await delay(600);

        let filtered = [...mockRequestLogs];

        // Apply filters
        if (filters.status && filters.status !== 'all') {
            filtered = filtered.filter(log => log.status === filters.status);
        }
        if (filters.server) {
            filtered = filtered.filter(log =>
                log.serverName.toLowerCase().includes(filters.server.toLowerCase())
            );
        }
        if (filters.command) {
            filtered = filtered.filter(log =>
                log.command.toLowerCase().includes(filters.command.toLowerCase())
            );
        }
        if (filters.search) {
            const search = filters.search.toLowerCase();
            filtered = filtered.filter(log =>
                log.userName.toLowerCase().includes(search) ||
                log.serverName.toLowerCase().includes(search) ||
                log.command.toLowerCase().includes(search) ||
                log.prompt.toLowerCase().includes(search)
            );
        }

        // Sort by timestamp (newest first)
        filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        // Pagination
        const start = (page - 1) * limit;
        const paged = filtered.slice(start, start + limit);

        return {
            data: paged,
            total: filtered.length,
            page,
            totalPages: Math.ceil(filtered.length / limit),
        };
    },

    // Get single log detail
    async getLogDetail(logId) {
        await delay(300);
        return mockRequestLogs.find(log => log.id === logId);
    },

    // Test bot message
    async testBotMessage({ message, mode = 'user', invocationType = 'prefix' }) {
        await delay(800 + Math.random() * 1200);

        const startTime = Date.now();

        // Simple mock responses based on message content
        let response = '';
        let error = null;

        if (message.toLowerCase().includes('help')) {
            response = `**Available Commands:**\n• \`!help\` - Show this help message\n• \`!ask [question]\` - Ask the AI anything\n• \`!kick @user [reason]\` - Kick a user\n• \`!ban @user [duration] [reason]\` - Ban a user`;
        } else if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
            response = `Hey there! 👋 How can I help you today?`;
        } else if (message.toLowerCase().includes('ask')) {
            response = `Great question! Let me think about that...\n\nBased on my training, I can provide you with some insights. This is a simulated AI response for testing purposes. In production, this would connect to your configured AI model.`;
        } else if (message.toLowerCase().includes('kick') || message.toLowerCase().includes('ban')) {
            if (mode === 'user') {
                error = 'You do not have permission to use this command.';
            } else {
                response = `✅ User has been ${message.toLowerCase().includes('kick') ? 'kicked' : 'banned'} successfully.`;
            }
        } else {
            response = `I received your message: "${message}"\n\nThis is a test response. Configure the bot's AI settings to get intelligent responses.`;
        }

        const executionTime = Date.now() - startTime;

        return {
            success: !error,
            response,
            error,
            executionTime,
            debug: {
                request: {
                    message,
                    mode,
                    invocationType,
                    timestamp: new Date().toISOString(),
                },
                processing: {
                    model: 'gpt-4-mock',
                    tokens: Math.floor(Math.random() * 500) + 100,
                },
            },
        };
    },

    // Export logs
    async exportLogs(format = 'json', filters = {}) {
        await delay(500);
        const { data } = await this.getRequestLogs({ limit: 1000, filters });

        if (format === 'json') {
            return JSON.stringify(data, null, 2);
        } else if (format === 'csv') {
            const headers = ['Timestamp', 'Server', 'Channel', 'User', 'Command', 'Type', 'Status', 'Time (ms)'];
            const rows = data.map(log => [
                log.timestamp,
                log.serverName,
                log.channelName,
                log.userName,
                log.command,
                log.invocationType,
                log.status,
                log.executionTime,
            ]);
            return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        }
    },
};

export default botApi;
