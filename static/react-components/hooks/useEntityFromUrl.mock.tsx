// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useEntityFromUrl';

export const useEntityFromUrl = fn(actual.useEntityFromUrl).mockName('useEntityFromUrl');
