// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { parseDiff } from 'react-diff-view';

import TitleDiffView from '#components/diffs/TitleDiffView';

const meta: Meta<typeof TitleDiffView> = {
    title: 'Components/Diffs/Components/TitleDiffView',
    component: TitleDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof TitleDiffView>;

// Mock diff data
const titleDiffString = `--- a/title
+++ b/title
@@ -1 +1 @@
-Original Task Title
+Updated Task Title with Changes`;

const longTitleDiffString = `--- a/title
+++ b/title
@@ -1 +1 @@
-This is a very long original task title that spans multiple words and demonstrates how the diff view handles longer content
+This is a very long updated task title that spans multiple words and demonstrates how the diff view handles longer content with significant modifications and additions`;

const mockDiff = parseDiff(titleDiffString);
const mockLongDiff = parseDiff(longTitleDiffString);

export const Primary: Story = {
    args: {
        originalValue: 'Original Task Title',
        changedValue: 'Updated Task Title with Changes',
        diff: mockDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Title change accepted'),
        onReject: () => console.log('Title change rejected'),
        onRollback: () => console.log('Title change rolled back'),
    },
};

export const LongTitle: Story = {
    args: {
        originalValue: 'This is a very long original task title that spans multiple words and demonstrates how the diff view handles longer content',
        changedValue: 'This is a very long updated task title that spans multiple words and demonstrates how the diff view handles longer content with significant modifications and additions',
        diff: mockLongDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Long title change accepted'),
        onReject: () => console.log('Long title change rejected'),
        onRollback: () => console.log('Long title change rolled back'),
    },
};

export const NoDiff: Story = {
    args: {
        originalValue: 'Same Title',
        changedValue: 'Same Title',
        diff: null,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('No diff accepted'),
        onReject: () => console.log('No diff rejected'),
        onRollback: () => console.log('No diff rolled back'),
    },
};

export const EmptyValues: Story = {
    args: {
        originalValue: null,
        changedValue: 'New Title Added',
        diff: parseDiff(`--- a/title
+++ b/title
@@ -1 +1 @@
-
+New Title Added`),
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Empty to value accepted'),
        onReject: () => console.log('Empty to value rejected'),
        onRollback: () => console.log('Empty to value rolled back'),
    },
};

export const ResolvedAccepted: Story = {
    args: {
        originalValue: 'Original Task Title',
        changedValue: 'Updated Task Title with Changes',
        diff: mockDiff,
        isResolved: true,
        resolvedValue: 'Updated Task Title with Changes',
        onAccept: () => console.log('Resolved title accepted'),
        onReject: () => console.log('Resolved title rejected'),
        onRollback: () => console.log('Resolved title rolled back'),
    },
};

export const ResolvedRejected: Story = {
    args: {
        originalValue: 'Original Task Title',
        changedValue: 'Updated Task Title with Changes',
        diff: mockDiff,
        isResolved: true,
        resolvedValue: 'Original Task Title',
        onAccept: () => console.log('Resolved title accepted'),
        onReject: () => console.log('Resolved title rejected'),
        onRollback: () => console.log('Resolved title rolled back'),
    },
};