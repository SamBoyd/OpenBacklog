// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';

import * as actual from './useAiChat';

export const useAiChat = fn(actual.useAiChat).mockName('useAiChat');

export default useAiChat;
