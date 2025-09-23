import  { Switch } from '@headlessui/react'
import React from 'react'
import { useState } from 'react'

export interface ToggleButtonProps {
    initialValue: boolean;
    useRef?: React.RefObject<HTMLButtonElement>;
    id?: string;
    title?: string;
    className?: string;
    disabled?: boolean;
    onClick: (event: React.MouseEvent) => void;
    dataTestId?: string;
    noBorder?: boolean;
    icon?: React.ReactNode;
    active?: boolean | string;
}

export const ToggleButton: React.FC<ToggleButtonProps> = ({ initialValue, useRef, onClick, className, dataTestId, id, disabled, ...props }) => {
    const [enabled, setEnabled] = useState(initialValue)

    return (
        <Switch
            ref={useRef}
            id={id}
            onClick={onClick}
            className={`
                ${className}
                ${enabled ? 'bg-primary/30' : 'bg-muted/15'}
                group relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-1 border-border transition-colors duration-200 ease-in-out focus:outline-none data-[checked]:bg-primary/30 py-0.5
            `}
            disabled={disabled}
            data-testid={dataTestId}
            {...props}
            checked={enabled}
            onChange={setEnabled}
        >
            <span className="sr-only">Use setting</span>
            <span className="pointer-events-none relative inline-block size-5 transform rounded-full bg-background shadow ring-0 transition duration-200 ease-in-out group-data-[checked]:translate-x-5">
                <span
                    aria-hidden="true"
                    className="absolute inset-0 flex size-full items-center justify-center text-muted-foreground  transition-opacity duration-200 ease-in group-data-[checked]:opacity-0 group-data-[checked]:duration-100 group-data-[checked]:ease-out"
                >
                    {/* Cross icon */}
                    <svg fill="currentColor" viewBox="0 0 12 12" className="size-full rounded-full">
                        <path
                            d="M4 8l2-2m0 0l2-2M6 6L4 4m2 2l2 2"
                            stroke="currentColor"
                            strokeWidth={1}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                    </svg>
                </span>

                <span
                    aria-hidden="true"
                    className="absolute inset-0 flex size-full items-center justify-center text-muted-foreground  opacity-0 transition-opacity duration-100 ease-out group-data-[checked]:opacity-100 group-data-[checked]:duration-200 group-data-[checked]:ease-in"
                >
                    {/* Tick icon */}
                    <svg fill="currentColor" viewBox="0 0 12 12" className="size-3" strokeWidth={1.5}>
                        <path d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z" />
                    </svg>
                </span>
            </span>
        </Switch>
    )
}