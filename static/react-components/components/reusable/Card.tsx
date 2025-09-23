import React from 'react';

interface CardProps {
    id?: string;
    children: React.ReactNode;
    className?: string;
    dataTestId?: string;
    onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ children, className, dataTestId, id, onClick }) => {
    return (
        <div
            id={id}
            data-testid={dataTestId}
            className={
                `text-foreground rounded
                 ${className} `
            }
            onClick={onClick}
        >
            {children}
        </div>
    );
};

export default Card;