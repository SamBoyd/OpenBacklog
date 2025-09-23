import React, { useState, useEffect } from 'react';
import { TaskStatus, statusDisplay } from '#types';
import { GrStatusPlaceholder } from 'react-icons/gr';
import { SelectBox } from './reusable/Selectbox';

interface StatusSelectProps {
    status: string;
    onChange: (status: string) => void;
    loading: boolean;
    className?: string;
    dataTestId?: string;
}

// Define status options with color mappings
const statusOptions = [
    {
        value: TaskStatus.TO_DO,
        label: statusDisplay(TaskStatus.TO_DO),
        bgColorClass: 'bg-status-todo',
        textColorClass: 'text-status-todo-foreground'
    },
    {
        value: TaskStatus.IN_PROGRESS,
        label: statusDisplay(TaskStatus.IN_PROGRESS),
        bgColorClass: 'bg-status-in-progress',
        textColorClass: 'text-status-in-progress-foreground'
    },
    {
        value: TaskStatus.DONE,
        label: statusDisplay(TaskStatus.DONE),
        bgColorClass: 'bg-status-done',
        textColorClass: 'text-status-done-foreground'
    },
];

const StatusSelect = ({
    status,
    onChange,
    loading,
    className,
    dataTestId
}: StatusSelectProps) => {
    const [selectedStatus, setSelectedStatus] = useState(status);

    useEffect(() => {
        setSelectedStatus(status);
    }, [status]);

    const handleStatusChange = (value: string) => {
        if (!loading) {
            setSelectedStatus(value);
            onChange(value);
        }
    };

    // Find selected status option to get color classes
    const selectedOption = statusOptions.find(option => option.value === selectedStatus) || statusOptions[0];

    return (
        <div className={`flex flex-row gap-4 w-full justify-start items-center ${className}`} data-testid={dataTestId}>
            <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                <GrStatusPlaceholder />
                <span className="ml-2.5 text-semibold">Status</span>
            </div>
            <div className="w-full">
                <SelectBox
                    value={selectedStatus}
                    onChange={handleStatusChange}
                    className={`max-w-[13rem] text-xl font-semibold ${selectedOption.textColorClass} border-transparent outline-none focus:border-transparent focus:ring-0`}
                    data-testid="status-select"
                    options={statusOptions}
                />
            </div>
        </div>
    );
}

export default StatusSelect;