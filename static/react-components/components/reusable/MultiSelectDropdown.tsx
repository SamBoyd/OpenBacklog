import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, X } from 'lucide-react';

/**
 * Represents an option in the multi-select dropdown.
 */
export interface MultiSelectOption {
  id: string;
  label: string;
  description?: string;
}

/**
 * Props for the MultiSelectDropdown component.
 */
interface MultiSelectDropdownProps {
  label: string;
  options: MultiSelectOption[];
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

/**
 * A multi-select dropdown component with checkboxes.
 * Users can select multiple options and see their selections as tags.
 *
 * @param props - The component props
 * @returns The MultiSelectDropdown component
 */
export const MultiSelectDropdown: React.FC<MultiSelectDropdownProps> = ({
  label,
  options,
  selectedIds,
  onChange,
  placeholder = 'Select...',
  className = '',
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedOptions = options.filter((opt) => selectedIds.includes(opt.id));
  const hasSelections = selectedOptions.length > 0;

  const filteredOptions = options.filter((option) =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!isOpen) {
      setSearchTerm('');
    } else if (searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current?.focus({ preventScroll: true });
      }, 50);
    }
  }, [isOpen]);

  /**
   * Toggles the selection of an option.
   */
  const handleToggleOption = (optionId: string): void => {
    if (selectedIds.includes(optionId)) {
      onChange(selectedIds.filter((id) => id !== optionId));
    } else {
      onChange([...selectedIds, optionId]);
    }
  };

  /**
   * Clears all selections.
   */
  const handleClearAll = (event: React.MouseEvent): void => {
    event.stopPropagation();
    onChange([]);
  };

  /**
   * Removes a single selection.
   */
  const handleRemoveSelection = (event: React.MouseEvent, optionId: string): void => {
    event.stopPropagation();
    onChange(selectedIds.filter((id) => id !== optionId));
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          flex items-center gap-2 px-3 py-2 
          bg-background border border-border rounded-lg
          text-sm text-foreground
          transition-colors duration-150
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary/50 cursor-pointer'}
          ${isOpen ? 'border-primary ring-1 ring-primary/20' : ''}
        `}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="text-foreground font-medium">{label}</span>

        {hasSelections ? (
          <span className="flex items-center gap-1">
            <span className="bg-primary/20 text-primary px-1.5 py-0.5 rounded text-xs font-medium">
              {selectedOptions.length}
            </span>
            <button
              type="button"
              onClick={handleClearAll}
              className="text-muted-foreground hover:text-foreground p-0.5 rounded"
              aria-label="Clear all selections"
            >
              <X size={14} />
            </button>
          </span>
        ) : (
          <span className="text-muted-foreground">{placeholder}</span>
        )}

        <ChevronDown
          size={16}
          className={`text-muted-foreground transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          className="
            absolute top-full left-0 mt-1 w-72 max-h-80
            bg-background rounded-lg shadow-lg border border-border
            text-foreground z-50 overflow-hidden
          "
          role="listbox"
          aria-multiselectable="true"
        >
          {options.length > 5 && (
            <div className="p-2 border-b border-border">
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search..."
                className="
                  w-full px-2 py-1.5 text-sm 
                  bg-muted/10 border border-border rounded
                  text-foreground placeholder:text-muted-foreground
                  focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary
                "
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          )}

          {hasSelections && (
            <div className="px-3 py-2 border-b border-border flex flex-wrap gap-1.5">
              {selectedOptions.map((option) => (
                <span
                  key={option.id}
                  className="
                    inline-flex items-center gap-1 px-2 py-0.5
                    bg-primary/15 text-primary rounded text-xs font-medium
                  "
                >
                  {option.label}
                  <button
                    type="button"
                    onClick={(e) => handleRemoveSelection(e, option.id)}
                    className="hover:text-primary/70"
                    aria-label={`Remove ${option.label}`}
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="overflow-y-auto max-h-52">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => {
                const isSelected = selectedIds.includes(option.id);

                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => handleToggleOption(option.id)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2 text-left
                      transition-colors duration-150
                      ${isSelected ? 'bg-primary/10' : 'hover:bg-muted/15'}
                    `}
                    role="option"
                    aria-selected={isSelected}
                  >
                    <div
                      className={`
                        w-4 h-4 rounded border flex items-center justify-center flex-shrink-0
                        transition-colors duration-150
                        ${isSelected ? 'bg-primary border-primary' : 'border-border'}
                      `}
                    >
                      {isSelected && <Check size={12} className="text-primary-foreground" />}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className="text-sm font-medium text-foreground truncate">
                        {option.label}
                      </span>
                      {option.description && (
                        <span className="text-xs text-muted-foreground truncate">
                          {option.description}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="px-3 py-4 text-sm text-muted-foreground text-center">
                No options found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

