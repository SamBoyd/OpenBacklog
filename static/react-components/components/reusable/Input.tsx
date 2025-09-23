import React from 'react';

export interface InputProps {
    id?: string;
    name?: string;
    type?: string;
    placeholder?: string;
    value?: string;
    checked?: boolean;
    disabled?: boolean;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onBlur?: () => void;
    onKeyDown?: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    className?: string;
    dataTestId?: string;
    autoFocus?: boolean;
}

const commonClasses = ` 
    block rounded-md px-2 py-1.5 text-base sm:text-sm/6 bg-muted/5 selected:bg-background/80
    border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
    `;

const compactCommonClasses = ` 
    block rounded-md px-2 py-0.5 text-sm bg-muted/5 selected:bg-background/80
    border border-primary/20 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
`;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({
    id,
    name,
    type,
    placeholder,
    value,
    onChange,
    onBlur,
    onKeyDown,
    className,
    dataTestId,
    disabled,
    autoFocus
}, ref) => {
    return (
        <input
            id={id}
            name={name}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            data-testid={dataTestId}
            disabled={disabled}
            ref={ref}
            className={`
                w-full
                ${commonClasses}
                ${className}
            `}
            autoFocus={autoFocus}
        />
    );
});

export const CompactInput = React.forwardRef<HTMLInputElement, InputProps>(({
    id,
    name,
    type,
    placeholder,
    value,
    onChange,
    onBlur,
    onKeyDown,
    className,
    dataTestId,
    disabled,
    autoFocus
}, ref) => {
    return (
        <input
            id={id}
            name={name}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            data-testid={dataTestId}
            disabled={disabled}
            ref={ref}
            className={`
                w-full text-xs
                ${compactCommonClasses}
                ${className}
            `}
            autoFocus={autoFocus}
        />
    );
});



export const CheckboxInput = React.forwardRef<HTMLInputElement, InputProps>(({
    id,
    name,
    checked,
    onChange,
    onBlur,
    onKeyDown,
    className,
    dataTestId,
    disabled,
    autoFocus
}, ref) => {
    return (
        <input
            id={id}
            name={name}
            type="checkbox"
            checked={checked || false}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            aria-label="Mark as completed"
            className={`
                accent-primary text-foreground
                w-fit block rounded-md text-base sm:text-sm/6 bg-transparent
                ${className}
            `}
            data-testid={dataTestId}
            disabled={disabled}
            ref={ref}
            autoFocus={autoFocus}
        />
    );
});

export const DateInput = React.forwardRef<HTMLInputElement, InputProps>(({
    id,
    name,
    type,
    placeholder,
    value,
    onChange,
    onBlur,
    onKeyDown,
    className,
    dataTestId,
    disabled,
    autoFocus
}, ref) => {
    return (
        <input
            id={id}
            name={name}
            type="date"
            value={value || ''}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            className={`
                w-full
                ${commonClasses}
                ${className}
            `}
            disabled={disabled}
            data-testid={dataTestId}
            ref={ref}
            autoFocus={autoFocus}
        />
    );
});

export const NumberInput = React.forwardRef<HTMLInputElement, InputProps>(({
    id,
    name,
    type,
    placeholder,
    value,
    onChange,
    onBlur,
    onKeyDown,
    className,
    dataTestId,
    disabled,
    autoFocus
}, ref) => {
    return (
        <input
            id={id}
            name={name}
            type="number"
            value={typeof (value) === 'number' ? value : Number(value)}
            onChange={onChange}
            onBlur={onBlur}
            onKeyDown={onKeyDown}
            className={`
                w-full
                ${commonClasses}
                ${className}
            `}
            disabled={disabled}
            data-testid={dataTestId}
            ref={ref}
            autoFocus={autoFocus}
        />
    );
});


interface ToggleProps {
    isEnabled: boolean;
    onChange: (isEnabled: boolean) => void;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

/**
 * A reusable toggle switch component
 */
export const Toggle: React.FC<ToggleProps> = ({
    isEnabled,
    onChange,
    size = 'md',
    className = ''
}) => {
    const sizeClasses = {
        sm: 'w-8 h-4',
        md: 'w-11 h-6',
        lg: 'w-14 h-7'
    };

    const thumbSizeClasses = {
        sm: 'w-3 h-3',
        md: 'w-4 h-4',
        lg: 'w-5 h-5'
    };

    return (
        <div
            onClick={() => onChange(!isEnabled)}
            className={`
                ${sizeClasses[size]} rounded-full flex items-center p-1 
                cursor-pointer transition-colors 
                ${isEnabled ? 'bg-primary justify-end' : 'bg-gray-300 justify-start'}
                ${className}
            `}
            role="switch"
            aria-checked={isEnabled}
        >
            <div className={`${thumbSizeClasses[size]} rounded-full bg-white`}></div>
        </div>
    );
};
