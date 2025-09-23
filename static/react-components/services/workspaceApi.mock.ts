import { fn } from '@storybook/test';

import * as actual from './workspaceApi'

export const fetchCurrentWorkspace = fn(actual.fetchCurrentWorkspace).mockName('fetchCurrentWorkspace');
