import { fn } from '@storybook/test';

import * as actual from '#hooks/diffs/useTaskDiff';

export const useTaskDiff = fn(actual.useTaskDiff).mockName('useTaskDiff');