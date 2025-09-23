import { fn } from '@storybook/test';

import * as actual from './useLocation';

export const useLocation = fn(actual.useLocation).mockName('useLocation');
