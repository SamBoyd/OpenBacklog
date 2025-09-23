// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useFieldDefinitions';

export const useFieldDefinitions = fn(actual.useFieldDefinitions).mockName('useFieldDefinitions');
