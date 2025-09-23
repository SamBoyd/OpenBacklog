import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

// Use require for the addon
// @ts-ignore
const { withRouter, reactRouterParameters } = require('storybook-addon-remix-react-router');

import { UserAccountStatus } from '#constants/userAccountStatus';

import BillingUsage from '#pages/BillingUsage';

import { useTasksContext } from '#contexts/TasksContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useWorkspaces } from '#hooks/useWorkspaces.mock';
import { useLocation } from '#hooks/useLocation.mock';
import { useBillingUsage, BillingUsageData, UseBillingUsageReturn } from '#hooks/useBillingUsage.mock';

import {
    mockAiImprovementsContextReturn,
    mockBillingUsageReturn,
    mockInitiativesContextReturn,
    mockLocationReturn,
    mockUseBillingUsageReturn,
    mockUseTasksContext,
    mockWorkspacesReturn,
} from '../example_data';

const mockUseBillingUsageReturnNewUser: UseBillingUsageReturn = {
    ...mockUseBillingUsageReturn,
    userIsOnboarded: false,
    data: {
        currentBalance: 0,
        transactions: [],
        transactionsPagination: null,
        subscriptionStatus: UserAccountStatus.NEW,
        monthlyCreditsTotal: 0,
        monthlyCreditsUsed: 200
    },
    userAccountDetails: {
        balanceCents: 0,
        status: UserAccountStatus.NEW,
        onboardingCompleted: true,
        monthlyCreditsTotal: 0,
        monthlyCreditsUsed: 0
    },
};

const meta: Meta<typeof BillingUsage> = {
    title: 'Pages/BillingUsage',
    component: BillingUsage,
    parameters: {
        layout: 'fullscreen',
        docs: {
            description: {
                component: 'Page for managing the users billing and usage analysis.',
            },
        },
        reactRouter: reactRouterParameters({
            routing: { path: '/workspace/billing' },
        }),
    },
    decorators: [
        withRouter,
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue(mockUseBillingUsageReturn);

            return <Story />
        }
    ],
} satisfies Meta<typeof BillingUsage>;

export default meta;

type Story = StoryObj<typeof BillingUsage>;

export const Primary: Story = {};

export const NoBalance: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                data: {
                    ...mockBillingUsageReturn,
                    currentBalance: 0,
                }
            });

            return <Story />
        }
    ]
};

export const NewUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturnNewUser,
                userAccountDetails: {
                    ...mockUseBillingUsageReturnNewUser.userAccountDetails,
                    status: UserAccountStatus.NEW,
                    balanceCents: 0,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 0,
                    monthlyCreditsUsed: 0
                }
            });

            return <Story />
        }
    ],
};


export const ClosedSubscriptionUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturnNewUser,
                userAccountDetails: {
                    ...mockUseBillingUsageReturnNewUser.userAccountDetails,
                    status: UserAccountStatus.CLOSED,
                    balanceCents: 0,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 0,
                    monthlyCreditsUsed: 0
                }
            });

            return <Story />
        }
    ],
};


export const NoSubscriptionUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturnNewUser,
                userAccountDetails: {
                    ...mockUseBillingUsageReturnNewUser.userAccountDetails,
                    status: UserAccountStatus.NO_SUBSCRIPTION,
                    balanceCents: 0,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 0,
                    monthlyCreditsUsed: 0
                }
            });

            return <Story />
        }
    ],
};

export const SuspendedUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                data: {
                    ...mockUseBillingUsageReturn.data,
                    currentBalance: 7.47,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 500,
                    subscriptionStatus: UserAccountStatus.SUSPENDED,
                },
                userAccountDetails: {
                    ...mockUseBillingUsageReturn.userAccountDetails,
                    status: UserAccountStatus.SUSPENDED,
                    balanceCents: 747,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 500
                }
            });

            return <Story />
        }
    ]
};

export const MeteredBillingUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                data: {
                    ...mockUseBillingUsageReturn.data,
                    currentBalance: 7.47,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 500,
                    subscriptionStatus: UserAccountStatus.METERED_BILLING,
                },
                userAccountDetails: {
                    ...mockUseBillingUsageReturn.userAccountDetails,
                    status: UserAccountStatus.METERED_BILLING,
                    balanceCents: 747,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 500
                }
            });

            return <Story />
        }
    ]
};

export const PaymentError: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                showErrorDialog: true,
            });

            return <Story />
        }
    ],
};

export const PaymentPending: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                showPendingDialog: true,
            })

            return <Story />
        }
    ]
};

export const PaymentCancelled: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                showCancelledDialog: true,
            });

            return <Story />
        }
    ]
};

export const RefundError: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                handleRefundRequest: () => Promise.resolve({ success: false, details: 'Refund failed. Please try again.' }),
            });

            return <Story />
        }
    ]
};

export const NoTransactions: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                data: {
                    ...mockBillingUsageReturn,
                    transactions: [],
                    transactionsPagination: {
                        totalCount: 0,
                        page: 1,
                        pageSize: 20,
                        hasNext: false
                    }
                }
            });

            return <Story />
        }
    ]
};

export const CancelledSubscriptionUser: Story = {
    args: {},
    decorators: [
        (Story) => {
            // Mock the hooks
            useLocation.mockReturnValue(mockLocationReturn);
            useWorkspaces.mockReturnValue(mockWorkspacesReturn);
            useTasksContext.mockReturnValue(mockUseTasksContext);
            useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
            useAiImprovementsContext.mockReturnValue(mockAiImprovementsContextReturn);
            useBillingUsage.mockReturnValue({
                ...mockUseBillingUsageReturn,
                data: {
                    ...mockBillingUsageReturn,
                    currentBalance: 0,
                },
                userAccountDetails: {
                    status: UserAccountStatus.ACTIVE_SUBSCRIPTION,
                    balanceCents: 0,
                    onboardingCompleted: false,
                    monthlyCreditsTotal: 500,
                    monthlyCreditsUsed: 0,
                    subscriptionCancelAt: '2026-01-01',
                    subscriptionCanceledAt: '2026-01-01',
                    subscriptionCancelAtPeriodEnd: true
                }
            });

            return <Story />
        }
    ]
};
