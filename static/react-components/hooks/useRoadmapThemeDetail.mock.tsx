// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useRoadmapThemeDetail';

export const useRoadmapThemeDetail = fn(actual.useRoadmapThemeDetail).mockName('useRoadmapThemeDetail');

export type { RoadmapThemeDetailData, MetricsData } from './useRoadmapThemeDetail';
