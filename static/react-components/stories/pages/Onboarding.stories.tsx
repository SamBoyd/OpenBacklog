import React from 'react';
// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { withRouter, reactRouterParameters } = require('storybook-addon-remix-react-router');

import Onboarding from '#pages/Onboarding';
import { useBillingUsage, BillingUsageData, UseBillingUsageReturn } from '#hooks/useBillingUsage.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { UserAccountStatus } from '#constants/userAccountStatus';
import { mockWorkspace, mockWorkspacesReturn } from '#stories/example_data';
import { WorkspaceDto } from '#types';

const mockOnboardCustomer = async () => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    alert('Page will now navigate away from onboarding')
}
// Mock the dependencies
const mockBillingUsageReturnNewUser: UseBillingUsageReturn = {
    data: {
        currentBalance: 0,
        transactions: [],
        transactionsPagination: null,
        subscriptionStatus: UserAccountStatus.NEW,
        monthlyCreditsTotal: 0,
        monthlyCreditsUsed: 0
    },
    userAccountDetails: {
        balanceCents: 0,
        status: UserAccountStatus.NEW,
        onboardingCompleted: false,
        monthlyCreditsTotal: 0,
        monthlyCreditsUsed: 0
    },
    userIsOnboarded: false,
    autoTopUp: false,
    setAutoTopUp: () => { },
    onboardCustomer: mockOnboardCustomer,
    setupMonthlySubscription: () => Promise.resolve(),
    handleAddCredit: () => console.log('Mock: Adding credit'),
    formatCurrency: (amount: number) => `$${amount.toFixed(2)}`,
    formatNumber: (num: number) => num.toLocaleString(),
    isLoading: false,
    isAccountDetailsLoading: false,
    error: null,
    showErrorDialog: false,
    showPendingDialog: false,
    showCancelledDialog: false,
    closeErrorDialog: () => { },
    closePendingDialog: () => { },
    closeCancelledDialog: () => { },
    handlePaymentRetry: () => { },
    handlePaymentSuccess: () => { },
    handlePaymentFailure: () => { },
    handleRefundRequest: async () => ({ success: true, details: 'Mock refund' }),
    handleOpenCustomerPortal: async () => { },
    loadTransactionsPage: () => { },
    resetTransactionsPagination: () => { },
    invalidateUserAccountDetails: async () => {
        console.log('invalidateUserAccountDetails')
        return Promise.resolve();
    }
};

const mockAddWorkspace = async (workspace: Omit<WorkspaceDto, 'id'>): Promise<WorkspaceDto> => {
    await new Promise((resolve) => setTimeout(resolve, 3000));
    return mockWorkspace
}

const meta = {
    title: 'Pages/Onboarding',
    component: Onboarding,
    parameters: {
        layout: 'fullscreen',
        docs: {
            description: {
                component: 'Carousel-style onboarding flow for new users. Guides users through product introduction, features, and pricing.',
            },
        },
        reactRouter: reactRouterParameters({
            routing: { path: '/onboarding' },
        }),
    },
    decorators: [
        withRouter,
        (Story) => {
            // Mock the hooks
            useBillingUsage.mockReturnValue(mockBillingUsageReturnNewUser);
            useWorkspaces.mockReturnValue({
                ...mockWorkspacesReturn,
                workspaces: [],
                currentWorkspace: null,
                addWorkspace: mockAddWorkspace,
            })
            return <Story />;
        }
    ],
    argTypes: {
        step: {
            control: 'select',
            options: ['planning', 'ai-assistants', 'coding-context', 'pricing'],
            description: 'Which step of onboarding to show',
        },
    },
} satisfies Meta<typeof Onboarding>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * The default onboarding carousel showing all steps.
 * Users can navigate through the carousel to see planning, AI assistants, coding context, and pricing.
 */
export const Default: Story = {
};

export const ExistingWorkspace: Story = {
    decorators: [
        (Story) => {
            useBillingUsage.mockReturnValue(mockBillingUsageReturnNewUser);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn)
            return <Story />;
        }
    ],
};