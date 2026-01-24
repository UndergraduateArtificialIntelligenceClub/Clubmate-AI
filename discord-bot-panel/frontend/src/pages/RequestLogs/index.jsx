import React, { useState, useEffect, useCallback } from 'react';
import {
    Search, Filter, Download, RefreshCw,
    ChevronDown, FileJson, FileSpreadsheet, X
} from 'lucide-react';
import { botApi } from '../../services/botApi';
import { useToast } from '../../components/global/ToastContext';
import { Button } from '../../components/global/Button';
import { Select } from '../../components/global/Select';
import { SkeletonTable } from '../../components/global/Skeleton';
import LogsTable from './LogsTable';
import LogDetailModal from './LogDetailModal';

const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'success', label: 'Success' },
    { value: 'error', label: 'Error' },
    { value: 'timeout', label: 'Timeout' },
];

export default function RequestLogs() {
    const { addToast } = useToast();
    const [logs, setLogs] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedLog, setSelectedLog] = useState(null);

    // Filters
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [sortConfig, setSortConfig] = useState({ key: 'timestamp', direction: 'desc' });

    // Pagination
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);

    const fetchLogs = useCallback(async () => {
        setIsLoading(true);
        try {
            const result = await botApi.getRequestLogs({
                page,
                limit: 20,
                filters: {
                    status: statusFilter,
                    search: searchQuery,
                }
            });
            setLogs(result.data);
            setTotalPages(result.totalPages);
            setTotal(result.total);
        } catch (error) {
            addToast('Failed to load logs', 'error');
        } finally {
            setIsLoading(false);
        }
    }, [page, statusFilter, searchQuery, addToast]);

    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const handleExport = async (format) => {
        try {
            const data = await botApi.exportLogs(format, {
                status: statusFilter,
                search: searchQuery
            });

            const blob = new Blob([data], {
                type: format === 'json' ? 'application/json' : 'text/csv'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `request-logs-${Date.now()}.${format}`;
            a.click();
            URL.revokeObjectURL(url);

            addToast(`Logs exported as ${format.toUpperCase()}`, 'success');
        } catch (error) {
            addToast('Export failed', 'error');
        }
    };

    const handleRefresh = () => {
        fetchLogs();
        addToast('Logs refreshed', 'info');
    };

    // Sort logs locally after fetch
    const sortedLogs = [...logs].sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        if (sortConfig.key === 'timestamp') {
            aVal = new Date(aVal);
            bVal = new Date(bVal);
        }

        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    return (
        <div className="animate-fadeIn">
            {/* Header */}
            <div style={{ marginBottom: '24px' }}>
                <h1 style={{ margin: 0, fontSize: '28px', fontWeight: 700 }}>Request Logs</h1>
                <p style={{ margin: '8px 0 0', color: 'var(--text-secondary)' }}>
                    Monitor real-time and historical requests from Discord servers
                </p>
            </div>

            {/* Filter Bar */}
            <div className="filter-bar">
                {/* Search */}
                <div style={{ flex: 1, minWidth: '250px', position: 'relative' }}>
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
                        placeholder="Search by user, server, or command..."
                        style={{ paddingLeft: '42px', width: '100%' }}
                    />
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            style={{
                                position: 'absolute',
                                right: '14px',
                                top: '50%',
                                transform: 'translateY(-50%)',
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                color: 'var(--text-secondary)',
                                padding: '4px'
                            }}
                        >
                            <X size={16} />
                        </button>
                    )}
                </div>

                {/* Status Filter */}
                <div style={{ minWidth: '150px' }}>
                    <Select
                        value={statusFilter}
                        onChange={(value) => { setStatusFilter(value); setPage(1); }}
                        options={statusOptions}
                    />
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px' }}>
                    <Button variant="ghost" onClick={handleRefresh}>
                        <RefreshCw size={16} />
                    </Button>
                    <div style={{ position: 'relative' }}>
                        <Button variant="ghost" onClick={() => handleExport('json')}>
                            <FileJson size={16} /> JSON
                        </Button>
                    </div>
                    <Button variant="ghost" onClick={() => handleExport('csv')}>
                        <FileSpreadsheet size={16} /> CSV
                    </Button>
                </div>
            </div>

            {/* Stats Bar */}
            <div style={{
                display: 'flex',
                gap: '24px',
                marginBottom: '24px',
                padding: '16px 20px',
                background: 'var(--glass-bg)',
                borderRadius: '12px'
            }}>
                <div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Total Requests</span>
                    <h3 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>{total}</h3>
                </div>
                <div style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '24px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Success Rate</span>
                    <h3 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600, color: 'var(--status-online)' }}>
                        {logs.length > 0
                            ? Math.round((logs.filter(l => l.status === 'success').length / logs.length) * 100)
                            : 0}%
                    </h3>
                </div>
                <div style={{ borderLeft: '1px solid var(--glass-border)', paddingLeft: '24px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Avg Response Time</span>
                    <h3 style={{ margin: '4px 0 0', fontSize: '20px', fontWeight: 600 }}>
                        {logs.length > 0
                            ? Math.round(logs.reduce((sum, l) => sum + l.executionTime, 0) / logs.length)
                            : 0}ms
                    </h3>
                </div>
            </div>

            {/* Table */}
            <div className="section-card" style={{ padding: 0, overflow: 'hidden' }}>
                {isLoading ? (
                    <div style={{ padding: '24px' }}>
                        <SkeletonTable rows={8} cols={6} />
                    </div>
                ) : (
                    <LogsTable
                        logs={sortedLogs}
                        sortConfig={sortConfig}
                        onSort={handleSort}
                        onRowClick={setSelectedLog}
                    />
                )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: '16px',
                    marginTop: '24px'
                }}>
                    <Button
                        variant="ghost"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                    >
                        Previous
                    </Button>
                    <span style={{ color: 'var(--text-secondary)' }}>
                        Page {page} of {totalPages}
                    </span>
                    <Button
                        variant="ghost"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                    >
                        Next
                    </Button>
                </div>
            )}

            {/* Detail Modal */}
            <LogDetailModal
                log={selectedLog}
                onClose={() => setSelectedLog(null)}
            />
        </div>
    );
}
