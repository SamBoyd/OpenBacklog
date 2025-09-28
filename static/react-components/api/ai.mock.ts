import { fn } from '@storybook/test';

import * as actual from './ai';

export const requestAiImprovement = fn(actual.requestAiImprovement).mockName('requestAiImprovement');
export const getAiImprovements = fn(actual.getAiImprovements).mockName('getAiImprovements');
export const markAiImprovementJobAsResolved = fn(actual.markAiImprovementJobAsResolved).mockName('markAiImprovementJobAsResolved');
