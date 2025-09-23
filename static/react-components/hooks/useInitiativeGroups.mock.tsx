// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';

import * as actual from './useInitiativeGroups';

export const useInitiativeGroups = fn(actual.useInitiativeGroups).mockName('useInitiativeGroups');
export const applySmartGroupCriteria = fn(actual.applySmartGroupCriteria).mockName('applySmartGroupCriteria');
    