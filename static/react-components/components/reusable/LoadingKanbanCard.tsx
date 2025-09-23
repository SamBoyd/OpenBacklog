import React from 'react';

import { Skeleton } from './Skeleton';


const LoadingKanbanCard = () => (
    <div className="card-template" data-testid="loading-card">
        <div className="e-card-content">
            <div className="card-template-wrap">
                <Skeleton type="paragraph" />
            </div>
        </div>
    </div>
);

export default LoadingKanbanCard;
