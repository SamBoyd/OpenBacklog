import React from 'react';

const disabledStyles = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';

export interface ButtonProps {
    useRef?: React.RefObject<HTMLButtonElement>;
    id?: string;
    title?: string;
    children: React.ReactNode;
    className?: string;
    disabled?: boolean;
    onClick: (event: React.MouseEvent) => void;
    dataTestId?: string;
    noBorder?: boolean;
    icon?: React.ReactNode;
    active?: boolean | string;
}

export const Button: React.FC<ButtonProps> = ({ useRef, children, title, onClick, className, dataTestId, id, disabled, noBorder, ...props }) => {
    return (
        <div className="relative rounded">
            <button
                ref={useRef}
                id={id}
                title={title}
                onClick={onClick}
                className={
                    `rounded ${className}
                 text-foreground bg-background
                 hover:bg-primary/10 
                 flex items-center justify-center
                 gap-x-1.5 px-2.5 py-1.5
                 ${noBorder ? 'border-none' : 'border border-border'}
                 ${disabledStyles}
                 `
                }
                disabled={disabled}
                data-testid={dataTestId}
                {...props}
            >
                {children}
            </button>
        </div>
    );
};

export const PrimaryButton: React.FC<ButtonProps> = ({ useRef, id, title, children, onClick, className, dataTestId, noBorder, disabled, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            title={title}
            onClick={onClick}
            className={
                `rounded ${className}
             text-foreground hover:bg-primary hover:text-primary-foreground
             border-border
             flex items-center justify-center
             gap-x-1.5 px-2.5 py-1.5
             ${noBorder ? 'border-none' : 'border'}
             ${disabledStyles}
             `
            }
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {children}
        </button>
    );
};

export const NoBorderButton: React.FC<ButtonProps> = ({ useRef, children, onClick, className, dataTestId, id, disabled, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            onClick={onClick}
            className={
                `rounded border-none 
                 text-foreground ${className}
                 hover:bg-primary/10 
                 flex items-center justify-center
                 gap-x-1.5 px-2.5 py-1.5
                 ${disabledStyles}
                 `
            }
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {children}
        </button>
    );
}


export const SecondaryButton: React.FC<ButtonProps> = ({ useRef, children, onClick, className, dataTestId, id, disabled, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            onClick={onClick}
            className={
                `rounded border border-border
                 text-muted-foreground ${className}
                 hover:bg-primary-foreground/10 
                 flex items-center justify-center
                 gap-x-1.5 px-2.5 py-1.5
                 ${disabledStyles}
                 `
            }
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {children}
        </button>
    );
};

export const IconButton: React.FC<ButtonProps> = ({ useRef, id, title, children, onClick, className, dataTestId, noBorder, disabled, icon, active, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            title={title}
            onClick={onClick}
            className={
                `rounded ${className}
             flex items-center justify-center
             gap-x-1.5 px-2.5 py-1.5
             ${noBorder ? 'border-none' : 'border border-border'}
             ${active ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-primary hover:text-primary-foreground'}
             ${disabledStyles}
             `
            }
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {icon}
            {title && <span>{title}</span>}
        </button>
    );
};


export const DangerButton: React.FC<ButtonProps> = ({ useRef, children, onClick, className, dataTestId, id, disabled, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            onClick={onClick}
            className={
                ` ${className}
                 rounded border border-border text-foreground bg-background 
                 hover:bg-destructive hover:text-destructive-foreground
                 hover:border-destructive
                 flex items-center justify-center
                 gap-x-1.5 px-2.5 py-1.5
                 ${disabledStyles}
                 `
            }
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {children}
        </button>
    );
};

interface ExpandingIconButtonProps extends Omit<ButtonProps, 'children'> {
    icon: React.ReactNode;
    title: string;
    onClick: (event: React.MouseEvent) => void;
    className?: string;
    dataTestId?: string;
    id?: string;
    disabled?: boolean;
    active?: boolean | string;
}

const ANIMATION_DURATION = 1200; // Duration in milliseconds
const ANIMATION_TIMING_FUNCTION = 'ease-in'
export const ExpandingIconButton: React.FC<ExpandingIconButtonProps> = ({ useRef, icon, title, onClick, className, dataTestId, id, disabled, active = false, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            onClick={onClick}
            className={
                `group relative flex items-center justify-center 
                 p-2 h-6
                 rounded border border-border
                 transition-transform duration-${ANIMATION_DURATION} ${ANIMATION_TIMING_FUNCTION} delay-150
                 ${active === true || active === "true"
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-sidebar text-sidebar-foreground '
                }
                 hover:w-auto hover:pl-2 hover:pr-3
                 focus:outline-none ${active === false || active === "false" ? 'focus:ring-1 focus:ring-ring focus:ring-offset-1' : ''}
                 disabled:pointer-events-none disabled:opacity-50
                 ${className}`
            }
            disabled={disabled}
            data-testid={dataTestId}
            title={title} // Add title attribute for accessibility when not expanded
            {...props}
        >
            <span className="flex items-center">
                {icon}
            </span>
            <span
                className={`absolute left-full ml-1 origin-left scale-x-0 transform whitespace-nowrap
                           opacity-0 transition-all duration-${ANIMATION_DURATION} ${ANIMATION_TIMING_FUNCTION} 
                           hover:delay-0 hover:duration-${ANIMATION_DURATION} hover:opacity-100
                           group-hover:relative group-hover:left-auto group-hover:ml-1.5 group-hover:scale-x-100 group-hover:opacity-100`}
            >
                {title}
            </span>
        </button>
    );
};

export const CompactButton: React.FC<ButtonProps> = ({ useRef, children, onClick, className, dataTestId, id, disabled, ...props }) => {
    return (
        <button
            ref={useRef}
            id={id}
            onClick={onClick}
            className={`rounded ${className} text-xs hover:bg-primary/10 px-2 py-1 ${disabledStyles}`}
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
        >
            {children}
        </button>
    );
};
