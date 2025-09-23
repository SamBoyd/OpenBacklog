import React, { useState, useRef, useEffect } from 'react';

// Define the structure for each option
interface SelectOption {
    value: string;
    label: string;
    color?: string;
}

// Update props: replace children with options, change onChange signature
interface SelectboxProps {
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
    variant?: 'default' | 'subtle'; // Add variant prop
}


export const SelectBox: React.FC<SelectboxProps> = ({
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
    variant = 'default',
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


    const handleOptionClick = (optionValue: string) => {
        onChange(optionValue); // Call the passed onChange handler
        setIsOpen(false); // Close the dropdown

    };

    return (
        <div className={`relative overflow-visible ${variant === 'subtle' ? 'group' : ''}`} ref={selectRef} data-testid={dataTestId}>
            {/* Hidden input to potentially help with form submissions if needed */}
            <input type="hidden" id={id} name={name} value={value} disabled={disabled} />

            {/* Button acting as the select trigger */}
            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={`
                    block max-w-56 px-3 py-2 text-left text-base sm:text-sm/6
                    transition-all duration-200
                    ${className}
                    ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    flex justify-between items-center
                    ${variant === 'subtle' 
                        ? `text-muted-foreground hover:text-foreground border-0 bg-transparent rounded-none px-0 py-1 ${isOpen || isOpen ? 'text-foreground' : ''}`
                        : `bg-background border border-border text-foreground rounded-md ${isOpen ? 'outline-none ring-1 ring-primary border-transparent' : ''}`
                    }
                `}
                disabled={disabled}
                aria-haspopup="listbox"
                aria-expanded={isOpen}
            >
                <span className="text-ellipsis overflow-hidden whitespace-nowrap">{selectedOptionLabel}</span>
                {/* Dropdown arrow icon - hidden for subtle variant unless focused/open */}
                <svg className={`w-5 h-5 ml-2 transform transition-all duration-200 
                    ${isOpen ? 'rotate-180' : ''} 
                    ${variant === 'subtle' ? `opacity-0 ${isOpen ? 'opacity-100' : 'group-hover:opacity-50'}` : 'opacity-100'}`} 
                    xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
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
                                        px-3 py-2 cursor-pointer text-sm hover:bg-primary hover:text-primary-foreground
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


export const CompactSelectBox: React.FC<SelectboxProps> = ({
    id,
    name,
    value,
    options,
    onChange,
    className,
    dataTestId,
    disabled,
    placeholder = 'Select an option',
    direction = 'down',
    searchBar = false,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const selectRef = useRef<HTMLDivElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

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
                searchInputRef.current?.focus();
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

        if (element === document.documentElement) {
            return document.documentElement;
        }

        const computedStyle = window.getComputedStyle(element);
        const overflowY = computedStyle.getPropertyValue('overflow-y');
        const isScrollable =
            overflowY === 'auto' ||
            overflowY === 'scroll' ||
            (overflowY === 'visible' && element === document.body);

        const hasScrollableContent = element.scrollHeight > element.clientHeight;

        if (isScrollable && hasScrollableContent) {
            return element;
        }

        return findScrollableParent(element.parentElement);
    };

    // Scroll dropdown into view when it opens
    useEffect(() => {
        if (isOpen && dropdownRef.current) {
            setTimeout(() => {
                if (!dropdownRef.current) return;

                const dropdownRect = dropdownRef.current.getBoundingClientRect();
                const scrollableParent = findScrollableParent(dropdownRef.current);

                let parentBottom;

                if (scrollableParent === document.documentElement) {
                    parentBottom = window.innerHeight;
                } else {
                    const parentRect = scrollableParent.getBoundingClientRect();
                    parentBottom = parentRect.top + scrollableParent.clientHeight;
                }

                if (dropdownRect.bottom > parentBottom) {
                    const scrollAmount = dropdownRect.bottom - parentBottom + 16;

                    scrollableParent.scrollBy({
                        top: scrollAmount,
                        behavior: 'smooth'
                    });
                }
            }, 50);
        }
    }, [isOpen]);

    if (!options || options.length === 0) {
        return <button
            type="button"
            onClick={() => { }}
            className={`
            block w-full rounded-md px-2 py-1 text-left text-xs bg-background
            border border-border text-foreground
            ${className}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            flex justify-between items-center
            ${isOpen ? 'outline-none ring-1 ring-primary border-transparent' : ''}
        `}
            disabled={disabled}
            aria-haspopup="listbox"
            aria-expanded={isOpen}
        >
            <span>{name}</span>
        </button>
    }

    const selectedOptionLabel = options.find(option => option.value === value)?.label || placeholder;

    const handleOptionClick = (optionValue: string) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    return (
        <div className="relative overflow-visible" ref={selectRef} data-testid={dataTestId}>
            <input type="hidden" id={id} name={name} value={value} disabled={disabled} />

            <button
                type="button"
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={`
                    block w-full rounded-md px-2 py-1 text-xs bg-background
                    border border-border text-foreground
                    ${className}
                    ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    flex justify-between items-center
                    ${isOpen ? 'outline-none ring-1 ring-primary border-transparent' : ''}
                `}
                disabled={disabled}
                aria-haspopup="listbox"
                aria-expanded={isOpen}
            >
                <span className="truncate">{selectedOptionLabel}</span>
                <svg className={`w-3 h-3 ml-1 transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
            </button>

            <div
                ref={dropdownRef}
                className={`
                z-20 w-40 h-auto mt-1 rounded-md bg-background text-foreground shadow-lg border border-border
                ${direction === 'up' ? 'absolute bottom-[calc(100%)]' : 'absolute top-[calc(100%)]'}
                transition-all duration-300
                ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
            `}>
                {searchBar && (
                    <div className="p-1 border-b border-border">
                        <input
                            ref={searchInputRef}
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Search..."
                            className="w-full px-1 py-0.5 text-xs bg-background border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
                            onClick={(e) => e.stopPropagation()}
                        />
                    </div>
                )}
                <ul
                    role="listbox"
                    className={`bg-background ${isOpen ? 'max-h-40' : 'h-0'} transition-all duration-300 overflow-y-auto`}
                    aria-activedescendant={value ? `option-${value}` : undefined}
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
                                    px-2 py-1 cursor-pointer text-xs hover:bg-primary hover:text-primary-foreground
                                    ${value === option.value ? 'bg-primary/20' : ''} flex items-center
                                `}
                            >
                                {option.label}
                            </li>
                        ))
                    ) : (
                        <li className="px-2 py-1 text-xs text-muted-foreground">
                            No options found
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
};