import React from 'react';
import { ChevronRight } from 'lucide-react';

interface OptionItemProps {
    option: string;
    bgColor?: string;
    textColor?: string;
    onEdit?: () => void;
    onDelete?: () => void;
    index: number;
}

/**
 * A reusable component for rendering an individual option item
 */
const OptionItem: React.FC<OptionItemProps> = ({
    option,
    bgColor = 'bg-blue-100',
    textColor = 'text-blue-800',
    onEdit,
    onDelete,
    index
}) => {
    return (
        <div
            className={`flex items-center p-2 rounded-md ${index % 2 === 0 ? 'bg-gray-100' : 'bg-gray-50'}`}
        >
            <div className="mr-2 flex flex-col items-center text-gray-400">
                <div className="grid grid-cols-2 gap-0.5">
                    <div className="w-1 h-1 rounded-full bg-current"></div>
                    <div className="w-1 h-1 rounded-full bg-current"></div>
                    <div className="w-1 h-1 rounded-full bg-current"></div>
                    <div className="w-1 h-1 rounded-full bg-current"></div>
                </div>
            </div>
            <div className={`flex-1 px-2 py-1 ${bgColor} ${textColor} rounded-md text-sm`}>
                {option}
            </div>
            <button
                onClick={onEdit}
                className="ml-2 text-gray-400"
            >
                <ChevronRight size={16} />
            </button>
        </div>
    );
};

export default OptionItem; 