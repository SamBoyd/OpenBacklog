// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useHeroes';

export const useHeroes = fn(actual.useHeroes).mockName('useHeroes');
