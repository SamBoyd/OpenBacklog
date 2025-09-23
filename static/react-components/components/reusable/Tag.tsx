import React from 'react';

type TagProps = {
    tag: string;
};

const Tag = ({ tag }: TagProps) => {
    return (
        <div
            data-testid="tag"
            className="py-0.5 px-1 rounded-md flex items-center h-fit bg-secondary"
        >
            <span className="tag">{tag}</span>
        </div>
    );
};

export default Tag;
