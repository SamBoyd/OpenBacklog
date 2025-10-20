// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useProductVision';

export const useProductVision = fn(actual.useProductVision).mockName('useProductVision');


