import React from 'react';
import { MdCreditCard } from 'react-icons/md';
import { PaymentMethodsResponse } from '#api/accounting';

/**
 * Props for the PaymentMethods component
 */
interface PaymentMethodsProps {
    paymentMethods: PaymentMethodsResponse | null;
    handleOpenCustomerPortal: () => Promise<void>;
}

/**
 * Payment methods component for managing payment methods
 * @param {PaymentMethodsProps} props - The component props
 * @returns {React.ReactElement} The payment methods component
 */
const PaymentMethods: React.FC<PaymentMethodsProps> = ({ paymentMethods, handleOpenCustomerPortal }) => {
    /**
     * Formats the card brand for display
     * @param {string} brand - The card brand from Stripe
     * @returns {string} The formatted brand name
     */
    const formatCardBrand = (brand: string): string => {
        switch (brand.toLowerCase()) {
            case 'visa':
                return 'Visa';
            case 'mastercard':
                return 'Mastercard';
            case 'american_express':
            case 'amex':
                return 'American Express';
            case 'discover':
                return 'Discover';
            case 'diners':
                return 'Diners Club';
            case 'jcb':
                return 'JCB';
            case 'unionpay':
                return 'UnionPay';
            default:
                return brand.charAt(0).toUpperCase() + brand.slice(1);
        }
    };

    return (
        <div className="border border-border rounded-lg p-4 text-foreground">
            <h3 className="text-lg text-muted-foreground font-semibold mb-3">Payment Methods</h3>
            <div className="space-y-2">
                {paymentMethods && paymentMethods.paymentMethods.length > 0 ? (
                    paymentMethods.paymentMethods.map((paymentMethod) => (
                        <div
                            key={paymentMethod.id}
                            className="flex items-center justify-between p-2 rounded text-foreground"
                        >
                            <div className="flex items-center gap-2">
                                <MdCreditCard className="text-lg" />
                                <span className="text-sm">
                                    {paymentMethod.cardBrand ? formatCardBrand(paymentMethod.cardBrand) : 'Card'}
                                    {paymentMethod.cardLast4 && ` •••• ${paymentMethod.cardLast4}`}
                                </span>
                            </div>

                            {paymentMethod.isDefault && (
                                <span className="ml-2 text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                                    Default
                                </span>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="text-sm text-muted-foreground p-2">
                        No payment methods found
                    </div>
                )}
                <button
                    onClick={handleOpenCustomerPortal}
                    className={`
                        w-full flex items-center justify-center gap-2 p-2 
                        border border-border rounded hover:bg-muted/5 transition-colors
                    `}
                >
                    <MdCreditCard className="text-lg" />
                    <span className="text-sm">Manage Payment Methods</span>
                </button>
            </div>
        </div>
    );
};

export default PaymentMethods; 