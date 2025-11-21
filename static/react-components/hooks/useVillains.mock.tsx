// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useVillains';

export const useVillains = fn(actual.useVillains).mockName('useVillains');
