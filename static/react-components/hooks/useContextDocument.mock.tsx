// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useContextDocument';

export const useContextDocument = fn(actual.useContextDocument).mockName('useContextDocument');
