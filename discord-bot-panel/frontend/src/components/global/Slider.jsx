import React, { useState, useRef, useEffect } from 'react';

export const Slider = ({
    value,
    onChange,
    min = 0,
    max = 100,
    step = 1,
    leftLabel,
    rightLabel,
    showValue = false
}) => {
    const trackRef = useRef(null);
    const [isDragging, setIsDragging] = useState(false);

    const percentage = ((value - min) / (max - min)) * 100;

    const handleMouseDown = (e) => {
        setIsDragging(true);
        updateValue(e);
    };

    const handleMouseMove = (e) => {
        if (!isDragging) return;
        updateValue(e);
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    const updateValue = (e) => {
        if (!trackRef.current) return;
        const rect = trackRef.current.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const pct = Math.max(0, Math.min(1, x / rect.width));
        const newValue = Math.round((pct * (max - min) + min) / step) * step;
        onChange(newValue);
    };

    useEffect(() => {
        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging]);

    return (
        <div className="slider-container">
            <div
                className="slider-track"
                ref={trackRef}
                onMouseDown={handleMouseDown}
            >
                <div className="slider-fill" style={{ width: `${percentage}%` }} />
                <div
                    className="slider-thumb"
                    style={{ left: `${percentage}%` }}
                />
            </div>
            <div className="slider-labels">
                <span>{leftLabel || min}</span>
                {showValue && <span style={{ color: 'var(--accent)', fontWeight: 500 }}>{value}</span>}
                <span>{rightLabel || max}</span>
            </div>
        </div>
    );
};

export default Slider;
