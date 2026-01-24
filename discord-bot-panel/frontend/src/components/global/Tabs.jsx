import React from 'react';

export const Tabs = ({ tabs, activeTab, onChange }) => {
    return (
        <div className="tabs-container">
            {tabs.map((tab) => (
                <button
                    key={tab.id}
                    className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => onChange(tab.id)}
                >
                    {tab.icon && <span style={{ marginRight: '8px' }}>{tab.icon}</span>}
                    {tab.label}
                </button>
            ))}
        </div>
    );
};

export default Tabs;
