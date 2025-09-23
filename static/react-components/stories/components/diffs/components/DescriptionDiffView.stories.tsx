// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { parseDiff } from 'react-diff-view';

import DescriptionDiffView from '#components/diffs/DescriptionDiffView';

const meta: Meta<typeof DescriptionDiffView> = {
    title: 'Components/Diffs/Components/DescriptionDiffView',
    component: DescriptionDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof DescriptionDiffView>;

// Mock diff data
const descriptionDiffString = `--- a/description
+++ b/description
@@ -1,3 +1,3 @@
 This is a task description
-that needs some improvements
+that has been significantly improved
 and additional details.`;

const multiLineDiffString = `--- a/description
+++ b/description
@@ -1,5 +1,7 @@
 # Task Overview
 
 This task involves implementing a new feature
-that will help users manage their projects better.
+that will help users manage their projects more effectively.
+
+## Additional Requirements
+- Must be mobile responsive`;

const emptyToContentDiffString = `--- a/description
+++ b/description
@@ -1 +1,3 @@
-
+This is a newly added description
+with multiple lines
+and detailed information.`;

const mockDiff = parseDiff(descriptionDiffString);
const mockMultiLineDiff = parseDiff(multiLineDiffString);
const mockEmptyToContentDiff = parseDiff(emptyToContentDiffString);

export const Primary: Story = {
    args: {
        originalValue: 'This is a task description\nthat needs some improvements\nand additional details.',
        changedValue: 'This is a task description\nthat has been significantly improved\nand additional details.',
        diff: mockDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Description change accepted'),
        onReject: () => console.log('Description change rejected'),
        onRollback: () => console.log('Description change rolled back'),
    },
};

export const MultiLineDescription: Story = {
    args: {
        originalValue: '# Task Overview\n\nThis task involves implementing a new feature\nthat will help users manage their projects better.',
        changedValue: '# Task Overview\n\nThis task involves implementing a new feature\nthat will help users manage their projects more effectively.\n\n## Additional Requirements\n- Must be mobile responsive',
        diff: mockMultiLineDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Multi-line description change accepted'),
        onReject: () => console.log('Multi-line description change rejected'),
        onRollback: () => console.log('Multi-line description change rolled back'),
    },
};

export const EmptyToContent: Story = {
    args: {
        originalValue: null,
        changedValue: 'This is a newly added description\nwith multiple lines\nand detailed information.',
        diff: mockEmptyToContentDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Empty to content accepted'),
        onReject: () => console.log('Empty to content rejected'),
        onRollback: () => console.log('Empty to content rolled back'),
    },
};

export const NoDiff: Story = {
    args: {
        originalValue: 'Same description content',
        changedValue: 'Same description content',
        diff: null,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('No diff accepted'),
        onReject: () => console.log('No diff rejected'),
        onRollback: () => console.log('No diff rolled back'),
    },
};

export const ResolvedAccepted: Story = {
    args: {
        originalValue: 'This is a task description\nthat needs some improvements\nand additional details.',
        changedValue: 'This is a task description\nthat has been significantly improved\nand additional details.',
        diff: mockDiff,
        isResolved: true,
        resolvedValue: 'This is a task description\nthat has been significantly improved\nand additional details.',
        onAccept: () => console.log('Resolved description accepted'),
        onReject: () => console.log('Resolved description rejected'),
        onRollback: () => console.log('Resolved description rolled back'),
    },
};

export const ResolvedRejected: Story = {
    args: {
        originalValue: 'This is a task description\nthat needs some improvements\nand additional details.',
        changedValue: 'This is a task description\nthat has been significantly improved\nand additional details.',
        diff: mockDiff,
        isResolved: true,
        resolvedValue: 'This is a task description\nthat needs some improvements\nand additional details.',
        onAccept: () => console.log('Resolved description accepted'),
        onReject: () => console.log('Resolved description rejected'),
        onRollback: () => console.log('Resolved description rolled back'),
    },
};