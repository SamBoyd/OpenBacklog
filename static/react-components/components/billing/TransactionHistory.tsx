import React from 'react';
import { MdChevronLeft, MdChevronRight, MdFirstPage } from 'react-icons/md';

/**
 * Transaction history component displaying transaction table with pagination
 * @param {object} props - Component props
 * @param {Array} props.transactions - Array of transaction objects
 * @param {string} props.formatCurrency - Function to format currency
 * @param {object} props.pagination - Pagination metadata
 * @param {function} props.onPageChange - Function to handle page changes
 * @param {function} props.onFirstPage - Function to go to first page
 * @returns {React.ReactElement} The transaction history component
 */
const TransactionHistory: React.FC<{
    transactions: Array<{
        id: number;
        date: string;
        type: string;
        amount: number;
    }>;
    pagination?: {
        totalCount: number;
        page: number;
        pageSize: number;
        hasNext: boolean;
    } | null;
    formatCurrency: (amount: number) => string;
    onPageChange: (page: number) => void;
    onFirstPage?: () => void;
}> = ({ transactions, pagination, formatCurrency, onPageChange, onFirstPage }) => {
    return (
        <div className="bg-card border border-border rounded-lg p-4">
            <h2 className="text-xl font-semibold mb-4">Transaction History</h2>
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-border">
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Date</th>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Type</th>
                            <th className="text-left py-2 text-sm font-medium text-muted-foreground">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions.map((transaction) => (
                            <tr key={transaction.id} className="border-b border-border/50">
                                <td className="py-3 text-sm">{transaction.date}</td>
                                <td className="py-3 text-sm">{transaction.type}</td>
                                <td className={`py-3 text-sm font-medium ${transaction.amount >= 0 ? 'text-green-600' : 'text-foreground'}`}>
                                    {formatCurrency(transaction.amount)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            {pagination && pagination.totalCount > 0 && (
                <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                    <div className="text-sm text-muted-foreground">
                        Showing {Math.min((pagination.page - 1) * pagination.pageSize + 1, pagination.totalCount)} to{' '}
                        {Math.min(pagination.page * pagination.pageSize, pagination.totalCount)} of{' '}
                        {pagination.totalCount} transactions
                    </div>
                    
                    <div className="flex items-center gap-2">
                        {/* Go to first page button - only show if page >= 2 */}
                        {pagination.page >= 2 && onFirstPage && (
                            <button
                                onClick={onFirstPage}
                                className="p-2 rounded border border-border hover:bg-muted transition-colors"
                                title="Go to first page"
                            >
                                <MdFirstPage className="w-4 h-4" />
                            </button>
                        )}
                        
                        {/* Previous page button */}
                        <button
                            onClick={() => onPageChange && onPageChange(pagination.page - 1)}
                            disabled={pagination.page <= 1}
                            className="p-2 rounded border border-border hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Previous page"
                        >
                            <MdChevronLeft className="w-4 h-4" />
                        </button>
                        
                        {/* Page numbers */}
                        <div className="flex items-center gap-1">
                            {(() => {
                                const currentPage = pagination.page;
                                const totalPages = Math.ceil(pagination.totalCount / pagination.pageSize);
                                const pages = [];
                                
                                // Always show first page
                                if (currentPage > 3) {
                                    pages.push(1);
                                    if (currentPage > 4) {
                                        pages.push('...');
                                    }
                                }
                                
                                // Show pages around current page
                                for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
                                    pages.push(i);
                                }
                                
                                // Always show last page
                                if (currentPage < totalPages - 2) {
                                    if (currentPage < totalPages - 3) {
                                        pages.push('...');
                                    }
                                    pages.push(totalPages);
                                }
                                
                                return pages.map((page, index) => (
                                    page === '...' ? (
                                        <span key={`ellipsis-${index}`} className="px-2 py-1 text-muted-foreground">
                                            ...
                                        </span>
                                    ) : (
                                        <button
                                            key={page}
                                            onClick={() => onPageChange && onPageChange(page as number)}
                                            className={`px-3 py-1 rounded border transition-colors ${
                                                page === currentPage
                                                    ? 'bg-primary text-primary-foreground border-primary'
                                                    : 'border-border hover:bg-muted'
                                            }`}
                                        >
                                            {page}
                                        </button>
                                    )
                                ));
                            })()}
                        </div>
                        
                        {/* Next page button */}
                        <button
                            onClick={() => onPageChange && onPageChange(pagination.page + 1)}
                            disabled={!pagination.hasNext}
                            className="p-2 rounded border border-border hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Next page"
                        >
                            <MdChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TransactionHistory; 