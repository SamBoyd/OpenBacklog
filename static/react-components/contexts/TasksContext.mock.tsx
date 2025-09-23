// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './TasksContext';

export const useTasksContext = fn(actual.useTasksContext).mockName('useTasksContext');
