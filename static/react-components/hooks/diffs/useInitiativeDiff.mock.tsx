import { fn } from '@storybook/test';

import * as actual from './useInitiativeDiff';

export const useInitiativeDiff = fn(actual.useInitiativeDiff).mockName('useInitiativeDiff');
