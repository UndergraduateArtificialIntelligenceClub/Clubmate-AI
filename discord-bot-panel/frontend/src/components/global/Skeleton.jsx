import React from 'react';

export const Skeleton = ({ variant = 'text', width, height, style }) => {
    const baseClass = `skeleton skeleton-${variant}`;

    return (
        <div
            className={baseClass}
            style={{
                width: width || undefined,
                height: height || undefined,
                ...style
            }}
        />
    );
};

export const SkeletonCard = ({ lines = 3 }) => (
    <div className="section-card" style={{ padding: '24px' }}>
        <Skeleton variant="title" width="40%" />
        {Array.from({ length: lines }).map((_, i) => (
            <Skeleton
                key={i}
                variant="text"
                width={`${100 - i * 15}%`}
                style={{ marginBottom: '12px' }}
            />
        ))}
    </div>
);

export const SkeletonTable = ({ rows = 5, cols = 4 }) => (
    <div style={{ overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
            {Array.from({ length: cols }).map((_, i) => (
                <Skeleton key={i} variant="text" width="120px" height="20px" />
            ))}
        </div>
        {Array.from({ length: rows }).map((_, rowIdx) => (
            <div key={rowIdx} style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
                {Array.from({ length: cols }).map((_, colIdx) => (
                    <Skeleton key={colIdx} variant="text" width="120px" />
                ))}
            </div>
        ))}
    </div>
);

export default Skeleton;
