import React from 'react';

/**
 * Rate card component displaying pricing information
 * @returns {React.ReactElement} The rate card component
 */
const RateCard: React.FC = () => {
    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg text-muted-foreground font-semibold mb-3">Rate Card</h3>
            <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                    <span>GPT-4 Input</span>
                    <span className="font-medium">$0.03/1K tokens</span>
                </div>
                <div className="flex justify-between">
                    <span>GPT-4 Output</span>
                    <span className="font-medium">$0.06/1K tokens</span>
                </div>
                <div className="flex justify-between">
                    <span>GPT-3.5 Input</span>
                    <span className="font-medium">$0.0015/1K tokens</span>
                </div>
                <div className="flex justify-between">
                    <span>GPT-3.5 Output</span>
                    <span className="font-medium">$0.002/1K tokens</span>
                </div>
            </div>
            <a href="#" className="text-primary text-sm hover:underline mt-3 inline-block">
                View full pricing →
            </a>
        </div>
    );
};

export default RateCard; 