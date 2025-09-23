// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useActiveEntity';

export const useActiveEntity = fn(actual.useActiveEntity).mockName('useActiveEntity');
export type UseActiveEntityReturn = actual.UseActiveEntityReturn;
export const ActiveEntityProvider = actual.ActiveEntityProvider;