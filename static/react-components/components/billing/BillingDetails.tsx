import React from 'react';
import { MdEdit } from 'react-icons/md';
import { BillingDetailsResponse } from '#api/accounting';

/**
 * Props for the BillingDetails component
 */
interface BillingDetailsProps {
    billingDetails: BillingDetailsResponse | null;
    handleOpenCustomerPortal: () => Promise<void>;
}

/**
 * Billing details component for displaying billing information from Stripe
 * @param {BillingDetailsProps} props - The component props
 * @returns {React.ReactElement} The billing details component
 */
const BillingDetails: React.FC<BillingDetailsProps> = ({ billingDetails, handleOpenCustomerPortal }) => {
    /**
     * Formats address parts into a single string
     * @param {object} details - The billing details object
     * @returns {string} Formatted address or empty string
     */
    const formatAddress = (details: BillingDetailsResponse['billingDetails']): string => {
        const addressParts = [
            details.addressLine1,
            details.addressLine2,
            details.addressCity,
            details.addressState,
            details.addressPostalCode,
            details.addressCountry
        ].filter(part => part && part.trim() !== '');
        
        return addressParts.join(', ');
    };

    const details = billingDetails?.billingDetails;

    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">Billing Details</h3>
                <button
                    onClick={handleOpenCustomerPortal}
                    className="flex items-center gap-2 px-3 py-1 text-sm text-primary hover:text-primary/80 transition-colors"
                >
                    <MdEdit className="text-sm" />
                    Edit Details
                </button>
            </div>

            {!details ? (
                <div className="text-sm text-muted-foreground">
                    Loading billing details...
                </div>
            ) : (
                <div className="space-y-3 text-sm">
                    <div>
                        <label className="block text-muted-foreground mb-1">Name</label>
                        <div className="text-foreground">
                            {details.name || 'Not provided'}
                        </div>
                    </div>

                    <div>
                        <label className="block text-muted-foreground mb-1">Email</label>
                        <div className="text-foreground">
                            {details.email || 'Not provided'}
                        </div>
                    </div>

                    <div>
                        <label className="block text-muted-foreground mb-1">Phone</label>
                        <div className="text-foreground">
                            {details.phone || 'Not provided'}
                        </div>
                    </div>

                    {formatAddress(details) && (
                        <div>
                            <label className="block text-muted-foreground mb-1">Address</label>
                            <div className="text-foreground">
                                {formatAddress(details)}
                            </div>
                        </div>
                    )}

                    {details.taxId && (
                        <div>
                            <label className="block text-muted-foreground mb-1">Tax ID</label>
                            <div className="text-foreground">
                                {details.taxId}
                            </div>
                        </div>
                    )}

                    <div className="pt-2 text-xs text-muted-foreground">
                        To update your billing information, click "Edit Details" to access the Stripe Customer Portal.
                    </div>
                </div>
            )}
        </div>
    );
};

export default BillingDetails; 