// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';

import * as actual from './isDeviceMobile';

export const useIsDeviceMobile = fn(actual.useIsDeviceMobile).mockName('useIsDeviceMobile');