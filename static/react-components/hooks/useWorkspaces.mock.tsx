// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useWorkspaces';

export const useWorkspaces = fn(actual.useWorkspaces).mockName('useWorkspaces');
