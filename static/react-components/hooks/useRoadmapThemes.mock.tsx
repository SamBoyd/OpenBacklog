// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';
import * as actual from './useRoadmapThemes';

export const useRoadmapThemes = fn(actual.useRoadmapThemes).mockName('useRoadmapThemes');
