// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useBillingUsage';

export const useBillingUsage = fn(actual.useBillingUsage).mockName('useBillingUsage');
export type BillingUsageData = actual.BillingUsageData;
export type UseBillingUsageReturn = actual.UseBillingUsageReturn;
