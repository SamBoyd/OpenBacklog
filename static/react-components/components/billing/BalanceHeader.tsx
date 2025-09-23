import React, { useRef, useState, useEffect } from 'react';
import { MdCreditCard, MdWarning, MdClose } from 'react-icons/md';
import { Loader2 } from 'lucide-react';

/**
 * Balance header component with top-up interface
 * @param {object} props - Component props
 * @param {number} props.currentBalance - Current account balance
 * @param {number} props.daysLeft - Days left at current burn rate
 * @param {boolean} props.autoTopUp - Auto top-up setting
 * @param {() => void} props.setAutoTopUp - Function to set auto top-up
 * @param {(amount: number) => void} props.handleAddCredit - Function to add credit
 * @param {string} props.formatCurrency - Function to format currency
 * @returns {React.ReactElement} The balance header component
 */
const BalanceHeader: React.FC<{
    currentBalance: number;
    daysLeft: number;
    autoTopUp: boolean;
    setAutoTopUp: (enabled: boolean) => void;
    handleAddCredit: (amount: number) => void;
    formatCurrency: (amount: number) => string;
}> = ({ currentBalance, daysLeft, autoTopUp, setAutoTopUp, handleAddCredit, formatCurrency }) => {
    const [showTopUpInterface, setShowTopUpInterface] = useState(false);
    const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
    const [customAmount, setCustomAmount] = useState<string>('');
    const [inputWidth, setInputWidth] = useState<number>(20);
    const [isLoading, setIsLoading] = useState(false);

    const customAmountInputRef = useRef<HTMLInputElement>(null);
    const hiddenSpanRef = useRef<HTMLSpanElement>(null);

    /**
     * Updates the input width based on the current value
     */
    useEffect(() => {
        if (hiddenSpanRef.current) {
            const text = customAmount || '0';
            hiddenSpanRef.current.textContent = text;
            const width = hiddenSpanRef.current.offsetWidth;
            setInputWidth(Math.max(width + 8, 20));
        }
    }, [customAmount]);

    /**
     * Handles the top-up process with the selected amount
     */
    const handleTopUp = async () => {
        const amount = selectedAmount || parseFloat(customAmount);
        if (amount && amount >= 1) {
            setIsLoading(true);
            try {
                await handleAddCredit(amount * 100);
                setShowTopUpInterface(false);
                setSelectedAmount(null);
                setCustomAmount('');
            } finally {
                setIsLoading(false);
            }
        }
    };

    /**
     * Handles selecting a preset amount
     */
    const handlePresetAmountSelect = (amount: number) => {
        setSelectedAmount(amount);
        setCustomAmount('');
    };

    /**
     * Handles custom amount input change
     */
    const handleCustomAmountChange = (value: string) => {
        setCustomAmount(value);
        setSelectedAmount(null);
    };

    /**
     * Validates if the current selection is valid for top-up
     */
    const isValidTopUpAmount = () => {
        const amount = selectedAmount || parseFloat(customAmount);
        return amount && amount >= 1;
    };

    return (
        <div>
            <h2 className="text-xl font-semibold mb-6">Usage Balance</h2>

            <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
                {/* Header Section */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8">
                    <div className="space-y-3">
                        <div className="flex flex-col gap-1">
                            <span className="text-base font-medium text-foreground">Current Balance</span>
                            <span className="text-xs text-muted-foreground/70 font-normal">
                                For AI usage beyond subscription
                            </span>
                        </div>
                        <div className="text-5xl font-black text-foreground tracking-tight">
                            {formatCurrency(currentBalance)}
                        </div>
                    </div>


                    <div className="flex flex-col items-end gap-2 min-w-fit">
                        {!showTopUpInterface ? (
                            <button
                                onClick={() => setShowTopUpInterface(true)}
                                className="group relative flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r rounded from-primary to-primary/90 text-primary-foreground rounded-xl hover:from-primary/90 hover:to-primary hover:shadow-lg hover:scale-[1.02] hover:rounded active:scale-[0.98] transition-all duration-200 font-semibold text-base shadow-md"
                            >
                                <MdCreditCard className="text-xl group-hover:rotate-12 transition-transform duration-200" />
                                <span>Top Up Balance</span>
                                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                            </button>
                        ) : null}
                    </div>
                </div>

                {/* Top-up Interface */}
                {showTopUpInterface && (
                    <div className="border-t border-border pt-8">
                        <div className="space-y-6">
                            <h3 className="text-lg font-semibold">Add Funds</h3>

                            {/* Preset Amounts */}
                            <div className="space-y-3">
                                <span className="text-sm font-medium text-muted-foreground">Quick amounts:</span>
                                <div className="flex flex-wrap gap-3">
                                    {[5, 10, 25, 50].map((amount) => (
                                        <button
                                            key={amount}
                                            onClick={() => handlePresetAmountSelect(amount)}
                                            disabled={isLoading}
                                            className={`px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium border-2 hover:scale-105 active:scale-95 ${selectedAmount === amount
                                                ? 'bg-primary text-primary-foreground border-primary shadow-md'
                                                : 'bg-background border-border text-foreground hover:bg-muted hover:border-primary/30 hover:shadow-sm'
                                                } disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100`}
                                        >
                                            ${amount}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Custom Amount */}
                            <div className="space-y-3">
                                <span className="text-sm font-medium text-muted-foreground">Or enter custom amount:</span>
                                <div className="flex items-center gap-4">
                                    <div
                                        onClick={() => !isLoading && customAmountInputRef.current?.focus()}
                                        className={`
                                            ${!isLoading ? 'cursor-text' : 'cursor-not-allowed'}
                                            flex items-center
                                            px-3 py-2 gap-2 border border-border rounded-lg bg-background text-sm
                                            ${customAmount && customAmount.length > 0
                                                ? 'ring-2 ring-primary ring-offset-2 ring-offset-background'
                                                : ''
                                            }
                                            ${isLoading ? 'opacity-50' : ''}
                                        `}
                                    >
                                        <span className="font-medium">$</span>
                                        <input
                                            name="customAmountInput"
                                            ref={customAmountInputRef}
                                            type="number"
                                            min="1"
                                            step="1"
                                            value={customAmount}
                                            onChange={(e) => handleCustomAmountChange(e.target.value)}
                                            disabled={isLoading}
                                            placeholder="0"
                                            style={{ width: `${Math.max(inputWidth, 60)}px` }}
                                            className="bg-transparent focus:outline-none disabled:cursor-not-allowed"
                                        />
                                        <span
                                            ref={hiddenSpanRef}
                                            className="absolute -left-full invisible text-sm"
                                            style={{ fontFamily: 'inherit', fontSize: 'inherit' }}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-4 pt-6">
                                <button
                                    onClick={handleTopUp}
                                    disabled={!isValidTopUpAmount() || isLoading}
                                    className="group relative flex items-center gap-3 px-8 py-3 bg-gradient-to-r from-primary to-primary/90 text-primary-foreground rounded-xl hover:from-primary/90 hover:to-primary hover:shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-semibold shadow-md"
                                >
                                    {isLoading ? (
                                        <Loader2 className="text-lg animate-spin" />
                                    ) : (
                                        <MdCreditCard className="text-lg group-hover:rotate-12 transition-transform duration-200" />
                                    )}
                                    <span>{isLoading ? 'Processing...' : 'Add Funds'}</span>
                                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                                </button>

                                <button
                                    onClick={() => {
                                        setShowTopUpInterface(false);
                                        setSelectedAmount(null);
                                        setCustomAmount('');
                                    }}
                                    className="px-6 py-3 text-muted-foreground hover:text-foreground transition-all duration-200 border-2 border-border rounded-xl hover:bg-muted hover:border-primary/30 hover:scale-105 active:scale-95 font-medium"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default BalanceHeader; 