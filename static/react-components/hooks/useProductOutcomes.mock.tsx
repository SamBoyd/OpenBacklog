// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useProductOutcomes';

export const useProductOutcomes = fn(actual.useProductOutcomes).mockName('useProductOutcomes');


