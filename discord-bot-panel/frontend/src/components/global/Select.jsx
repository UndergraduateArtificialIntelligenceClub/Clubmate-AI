import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

export const Select = ({
    value,
    onChange,
    options,
    placeholder = 'Select...',
    renderOption,
    renderValue
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);

    const selectedOption = options.find(opt => opt.value === value);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="select-wrapper" ref={wrapperRef}>
            <div
                className="select-trigger"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span>
                    {selectedOption
                        ? (renderValue ? renderValue(selectedOption) : selectedOption.label)
                        : placeholder
                    }
                </span>
                <ChevronDown
                    size={18}
                    style={{
                        transition: 'transform 150ms ease',
                        transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)'
                    }}
                />
            </div>

            {isOpen && (
                <div className="select-dropdown">
                    {options.map((option) => (
                        <div
                            key={option.value}
                            className={`select-option ${value === option.value ? 'selected' : ''}`}
                            onClick={() => {
                                onChange(option.value);
                                setIsOpen(false);
                            }}
                        >
                            {renderOption ? renderOption(option) : option.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Select;
