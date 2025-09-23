import { fn } from '@storybook/test';

import * as actual from './tasks';

export const postTask = fn(actual.postTask).mockName('postTask');
