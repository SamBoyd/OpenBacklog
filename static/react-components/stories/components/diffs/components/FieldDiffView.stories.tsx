// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { parseDiff } from 'react-diff-view';

import FieldDiffView from '#components/diffs/FieldDiffView';

const meta: Meta<typeof FieldDiffView> = {
    title: 'Components/Diffs/Components/FieldDiffView',
    component: FieldDiffView,
    parameters: {
        layout: 'padded',
    },
};

export default meta;
type Story = StoryObj<typeof FieldDiffView>;

// Mock diff data for different scenarios
const titleDiffString = `--- a/title
+++ b/title
@@ -1 +1 @@
-Original Title
+Updated Title`;

const descriptionDiffString = `--- a/description
+++ b/description
@@ -1,3 +1,4 @@
 This is the original description
-that needs some updates
+that has been significantly improved
 and contains multiple lines.
+Additional content has been added.`;

const complexDiffString = `--- a/field
+++ b/field
@@ -1,10 +1,12 @@
 # Header
 
 This is a complex field with:
-* Old bullet point
+* Updated bullet point
 * Another point
 
-Some text that will be changed.
+Some text that has been modified significantly.
+
+## New Section
+Additional content added here.
 
 Final line.`;

const mockTitleDiff = parseDiff(titleDiffString);
const mockDescriptionDiff = parseDiff(descriptionDiffString);
const mockComplexDiff = parseDiff(complexDiffString);

export const TitleField: Story = {
    args: {
        fieldName: 'title',
        originalValue: 'Original Title',
        changedValue: 'Updated Title',
        diff: mockTitleDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Title field accepted'),
        onReject: () => console.log('Title field rejected'),
        onRollback: () => console.log('Title field rolled back'),
    },
};

export const DescriptionField: Story = {
    args: {
        fieldName: 'description',
        originalValue: 'This is the original description\nthat needs some updates\nand contains multiple lines.',
        changedValue: 'This is the original description\nthat has been significantly improved\nand contains multiple lines.\nAdditional content has been added.',
        diff: mockDescriptionDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Description field accepted'),
        onReject: () => console.log('Description field rejected'),
        onRollback: () => console.log('Description field rolled back'),
    },
};

export const ComplexDiff: Story = {
    args: {
        fieldName: 'description',
        originalValue: '# Header\n\nThis is a complex field with:\n* Old bullet point\n* Another point\n\nSome text that will be changed.\n\nFinal line.',
        changedValue: '# Header\n\nThis is a complex field with:\n* Updated bullet point\n* Another point\n\nSome text that has been modified significantly.\n\n## New Section\nAdditional content added here.\n\nFinal line.',
        diff: mockComplexDiff,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Complex diff accepted'),
        onReject: () => console.log('Complex diff rejected'),
        onRollback: () => console.log('Complex diff rolled back'),
    },
};

export const NoDiff: Story = {
    args: {
        fieldName: 'title',
        originalValue: 'Same content',
        changedValue: 'Same content',
        diff: null,
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('No diff accepted'),
        onReject: () => console.log('No diff rejected'),
        onRollback: () => console.log('No diff rolled back'),
    },
};

export const EmptyDiff: Story = {
    args: {
        fieldName: 'title',
        originalValue: 'Some content',
        changedValue: 'Different content',
        diff: [],
        isResolved: false,
        resolvedValue: null,
        onAccept: () => console.log('Empty diff accepted'),
        onReject: () => console.log('Empty diff rejected'),
        onRollback: () => console.log('Empty diff rolled back'),
    },
};

export const ResolvedAccepted: Story = {
    args: {
        fieldName: 'title',
        originalValue: 'Original Title',
        changedValue: 'Updated Title',
        diff: mockTitleDiff,
        isResolved: true,
        resolvedValue: 'Updated Title',
        onAccept: () => console.log('Resolved field accepted'),
        onReject: () => console.log('Resolved field rejected'),
        onRollback: () => console.log('Resolved field rolled back'),
    },
};

export const ResolvedRejected: Story = {
    args: {
        fieldName: 'title',
        originalValue: 'Original Title',
        changedValue: 'Updated Title',
        diff: mockTitleDiff,
        isResolved: true,
        resolvedValue: 'Original Title',
        onAccept: () => console.log('Resolved field accepted'),
        onReject: () => console.log('Resolved field rejected'),
        onRollback: () => console.log('Resolved field rolled back'),
    },
};

export const ResolvedWithNullValue: Story = {
    args: {
        fieldName: 'description',
        originalValue: 'Original description',
        changedValue: 'Updated description',
        diff: mockDescriptionDiff,
        isResolved: true,
        resolvedValue: null,
        onAccept: () => console.log('Resolved with null accepted'),
        onReject: () => console.log('Resolved with null rejected'),
        onRollback: () => console.log('Resolved with null rolled back'),
    },
};