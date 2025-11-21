// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useConflicts';

export const useConflicts = fn(actual.useConflicts).mockName('useConflicts');
