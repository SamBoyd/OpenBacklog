// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './SuggestionsToBeResolvedContext';

export const useSuggestionsToBeResolved = fn(actual.useSuggestionsToBeResolved).mockName('useSuggestionsToBeResolved');
