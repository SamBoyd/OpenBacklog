// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useStrategicPillars';

export const useStrategicPillars = fn(actual.useStrategicPillars).mockName('useStrategicPillars');
