import React from 'react';
import { EntityType, FieldType } from '#types';
import {
    Type,
    Hash,
    ListChecks,
    CheckSquare,
    Calendar,
    CheckCircle,
    Link2,
    Mail,
    Phone,
    Tag,
    ArrowLeft,
    ChevronRight,
} from 'lucide-react';

interface PanelFieldTypeProps {
    onSelectFieldType: (fieldType: FieldType) => void;
}

/**
 * Component for selecting a field type
 */
const PanelFieldType: React.FC<PanelFieldTypeProps> = ({ onSelectFieldType }) => {

    /**
     * Returns the icon for a given field type
     * @param {FieldType} fieldType - The field type to get the icon for
     * @returns {React.ReactNode} The icon for the field type
     */
    const getIconForField = (fieldType: FieldType) => {
        switch (fieldType) {
            case FieldType.TEXT:
                return <Type size={16} />;
            case FieldType.NUMBER:
                return <Hash size={16} />;
            case FieldType.SELECT:
                return <Tag size={16} />;
            case FieldType.MULTI_SELECT:
                return <ListChecks size={16} />;
            case FieldType.STATUS:
                return <CheckCircle size={16} />;
            case FieldType.DATE:
                return <Calendar size={16} />;
            case FieldType.CHECKBOX:
                return <CheckSquare size={16} />;
            case FieldType.URL:
                return <Link2 size={16} />;
            case FieldType.EMAIL:
                return <Mail size={16} />;
            case FieldType.PHONE:
                return <Phone size={16} />;
        }
    };

    /**
     * Formats the field type name for display
     * @param {FieldType} fieldType - The field type to format
     * @returns {string} The formatted field type name
     */
    const formatFieldTypeName = (fieldType: FieldType): string => {
        return fieldType.replace(/_/g, " ").toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    return (
        <div className="flex-grow p-4 bg-background text-foreground rounded-lg shadow-lg w-64 mb-4">
            <div className="flex justify-start items-center mb-4 pb-2 border-b border-border">
                <span className="text-sm text-muted">New field</span>
            </div>

            <div className="flex flex-col">
                {Object.values(FieldType).map((fieldType) => (
                    <button
                        key={fieldType}
                        onClick={() => onSelectFieldType(fieldType)}
                        className="flex flex-row gap-2 items-center justify-between text-left px-1 py-1 hover:bg-muted/15 rounded"
                    >

                        <div className="flex flex-row gap-2 items-center">
                            {getIconForField(fieldType)}
                            {formatFieldTypeName(fieldType)}
                        </div>

                        <ChevronRight size={16} className="text-muted-foreground/50" />
                    </button>
                ))}
            </div>

        </div>
    );
};

export default PanelFieldType; 