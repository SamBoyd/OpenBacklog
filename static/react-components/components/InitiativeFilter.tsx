import React, { useState, useRef, useEffect } from 'react';

// Define the structure for each option
interface SelectOption {
    value: string;
    label: string;
    color?: string;
}

// Update props: replace children with options, change onChange signature
interface InitiativeFilterProps {
    id?: string;
    name?: string;
    value?: string; // The currently selected value
    options: SelectOption[]; // Array of options
    onChange: (value: string) => void; // Callback with the selected value
    className?: string;
    dataTestId?: string;
    disabled?: boolean;
    placeholder?: string; // Optional placeholder
    direction?: 'down' | 'up';
    searchBar?: boolean;
    dropdownWidth?: string;
    dropdownMaxHeight?: string;
}

export const InitiativeFilter: React.FC<InitiativeFilterProps> = ({
    id,
    name,
    value,
    options,
    onChange,
    className,
    dataTestId,
    disabled,
    placeholder = 'Select an option', // Default placeholder
    direction = 'down',
    dropdownWidth = '52',
    dropdownMaxHeight,
    searchBar = false,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const selectRef = useRef<HTMLDivElement>(null); // Ref for the main container
    const dropdownRef = useRef<HTMLDivElement>(null); // Ref for the dropdown element
    const searchInputRef = useRef<HTMLInputElement>(null); // Ref for the search input

    // Filter options based on search term
    const filteredOptions = searchBar ?
        options.filter(option =>
            option.label.toLowerCase().includes(searchTerm.toLowerCase())
        ) : options;

    // Reset search term when dropdown closes
    useEffect(() => {
        if (!isOpen) {
            setSearchTerm('');
        } else if (searchBar && searchInputRef.current) {
            // Focus search input when dropdown opens
            setTimeout(() => {
                searchInputRef.current?.focus({ preventScroll: true });
            }, 50);
        }
    }, [isOpen, searchBar]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    // Find the first scrollable parent of an element
    const findScrollableParent = (element: HTMLElement | null): HTMLElement => {
        if (!element) return document.documentElement;

        // Check if the element is the root
        if (element === document.documentElement) {
            return document.documentElement;
        }

        // Get computed style to check overflow properties
        const computedStyle = window.getComputedStyle(element);
        const overflowY = computedStyle.getPropertyValue('overflow-y');
        const isScrollable =
            overflowY === 'auto' ||
            overflowY === 'scroll' ||
            (overflowY === 'visible' && element === document.body);

        // Check if element has scrollable content
        const hasScrollableContent = element.scrollHeight > element.clientHeight;

        if (isScrollable && hasScrollableContent) {
            return element;
        }

        // Recursively check parent
        return findScrollableParent(element.parentElement);
    };

    // Scroll dropdown into view when it opens and extends below viewport
    useEffect(() => {
        if (isOpen && dropdownRef.current) {
            // Small delay to ensure the dropdown is fully rendered
            setTimeout(() => {
                if (!dropdownRef.current) return;

                // Get the dropdown's position and dimensions
                const dropdownRect = dropdownRef.current.getBoundingClientRect();

                // Find the scrollable parent
                const scrollableParent = findScrollableParent(dropdownRef.current);

                // Get the parent's viewport bounds
                let parentBottom;

                if (scrollableParent === document.documentElement) {
                    // If the scrollable parent is the document, use window height
                    parentBottom = window.innerHeight;
                } else {
                    // Otherwise use the parent's bounds
                    const parentRect = scrollableParent.getBoundingClientRect();
                    parentBottom = parentRect.top + scrollableParent.clientHeight;
                }

                // Check if the bottom of the dropdown is below the parent's viewport
                if (dropdownRect.bottom > parentBottom) {
                    // Calculate how much we need to scroll to make the dropdown fully visible
                    const scrollAmount = dropdownRect.bottom - parentBottom + 16; // Add a small buffer

                    // Scroll the parent to make the dropdown visible
                    scrollableParent.scrollBy({
                        top: scrollAmount,
                        behavior: 'smooth'
                    });
                }
            }, 50); // Small delay to ensure dropdown is rendered
        }
    }, [isOpen]);

    if (!options || options.length === 0) {
        return <button
            type="button"
            onClick={() => { }}
            className={`
            block w-full rounded-md px-3 py-2 text-left text-base sm:text-sm/6 bg-background
            border border-border text-foreground
            transition-width duration-1000
            ${className}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            flex justify-between items-center // Align text and icon
            ${isOpen ? 'outline-none ring-1 ring-primary border-transparent' : ''}
        `}
            disabled={disabled}
            aria-haspopup="listbox"
            aria-expanded={isOpen}
        >
            <span>{name}</span>
        </button>
    }

    // Find the label for the currently selected value
    const selectedOptionLabel = options.find(option => option.value === value)?.label || placeholder;

    const optionSelected = selectedOptionLabel !== placeholder;

    // Marquee effect state and refs
    const labelContainerRef = useRef<HTMLDivElement>(null);
    const labelTextRef = useRef<HTMLSpanElement>(null);
    const [isLabelOverflowing, setIsLabelOverflowing] = useState(false);
    const [isHovered, setIsHovered] = useState(false);

    // Check if label is overflowing
    useEffect(() => {
        setTimeout(() => {
            if (labelContainerRef.current && labelTextRef.current) {
                setIsLabelOverflowing(labelTextRef.current.scrollWidth > labelContainerRef.current.clientWidth);
            }
        }, 0);
    }, [selectedOptionLabel, isOpen]);


    const handleOptionClick = (optionValue: string) => {
        onChange(optionValue); // Call the passed onChange handler
        setIsOpen(false); // Close the dropdown

    };

    return (
        <div className="relative overflow-visible" ref={selectRef} data-testid={dataTestId}>
            {/* Hidden input to potentially help with form submissions if needed */}
            <input type="hidden" id={id} name={name} value={value} disabled={disabled} />

            {/* Button acting as the select trigger */}
            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={`
                    block max-w-56 rounded-md px-3 py-2 text-left text-base sm:text-sm/6 bg-background
                    border border-border text-foreground
                    transition-width duration-1000
                    ${className ? className : ''}
                    ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    flex justify-between items-center
                    ${isOpen ? 'outline-none ring-1 ring-primary border-transparent' : ''}
                `}
                disabled={disabled}
                aria-haspopup="listbox"
                aria-expanded={isOpen}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                <div
                    ref={labelContainerRef}
                    className="relative flex-1 min-w-0 overflow-hidden"
                    style={{ maxWidth: 'calc(100% - 2rem)' }}
                >
                    {isLabelOverflowing ? (
                        <div
                            className={`flex ${isHovered && optionSelected ? 'animate-marquee' : ''}`}
                            // style={{
                            //     width: labelWidth ? `${labelWidth * 2}px` : 'auto',
                            //     transform: optionSelected && isHovered ? `translateX(-${labelWidth}px)` : 'translateX(0)',
                            //     transition: optionSelected && isHovered ? 'transform 3s linear' : 'transform 0.3s',
                            // }}
                            onMouseEnter={() => setIsHovered(true)}
                            onMouseLeave={() => setIsHovered(false)}
                        >
                            <span ref={labelTextRef} className="block whitespace-nowrap">
                                {selectedOptionLabel}
                            </span>
                        </div>
                    ) : (
                        <span ref={labelTextRef} className="block whitespace-nowrap text-ellipsis overflow-hidden">
                            {selectedOptionLabel}
                        </span>
                    )}
                </div>
                {/* Dropdown arrow icon */}
                <svg className={`w-5 h-5 ml-2 transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
            </button>

            {/* Dropdown panel */}
            <div
                ref={dropdownRef}
                className={`
                absolute z-20  mt-1 rounded-md bg-background text-foreground shadow-lg border border-border
                ${dropdownWidth ? `w-${dropdownWidth}` : 'w-52'}
                ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
            `}>

                {searchBar && (
                    <div className="p-2 border-b border-border">
                        <input
                            ref={searchInputRef}
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search options..."
                            className="w-full px-2 py-1 text-sm bg-background border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                )}
                <ul
                    role="listbox"
                    className={`bg-background overflow-scroll ${dropdownMaxHeight ? `h-${dropdownMaxHeight}` : ''}`}
                    aria-activedescendant={value ? `option-${value}` : undefined} // Highlight selected option if value exists
                >
                    {filteredOptions.length > 0 ? (
                        filteredOptions.map((option, index) => (
                            <li
                                key={`option-${option.value}-${index}`}
                                id={`option-${option.value}-${index}`}
                                role="option"
                                aria-selected={value === option.value}
                                onClick={() => handleOptionClick(option.value)}
                                className={`
                                        px-3 py-1 cursor-pointer text-sm hover:bg-primary/15 hover:text-primary-foreground
                                        ${value === option.value ? 'bg-primary/20' : ''} flex items-center
                                    `}
                            >
                                {option.label}
                            </li>
                        ))
                    ) : (
                        <li className="px-3 py-2 text-sm text-muted-foreground">
                            No options found
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
};