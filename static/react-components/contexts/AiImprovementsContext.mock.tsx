// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './AiImprovementsContext';

export const useAiImprovementsContext = fn(actual.useAiImprovementsContext).mockName('useAiImprovementsContext');

export const AiImprovementsContextProvider = fn(actual.AiImprovementsContextProvider).mockName('AiImprovementsContextProvider');
