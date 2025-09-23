// eslint-disable-next-line n/no-unpublished-import
import { fn } from '@storybook/test';

import * as actual from './useChatMessages';

const useChatMessages = fn(actual.useChatMessages).mockName('useChatMessages');

export default useChatMessages;