import { fn } from '@storybook/test';
import * as actual from './useParams';

export const useParams = fn(actual.useParams).mockName('useParams');
