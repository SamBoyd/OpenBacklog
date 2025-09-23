import { fn } from '@storybook/test';

import * as actual from './initiatives';

export const postInitiative = fn(actual.postInitiative).mockName('postInitiative');
