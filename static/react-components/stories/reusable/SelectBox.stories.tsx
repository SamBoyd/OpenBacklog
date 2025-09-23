import React, { useState } from 'react';

import type { Meta, StoryObj } from '@storybook/react';
import { SelectBox } from '#components/reusable/Selectbox';
import { TaskStatus, statusDisplay } from '#types';


const meta: Meta<typeof SelectBox> = {
    component: SelectBox,
}

export default meta;
type Story = StoryObj<typeof SelectBox>;


const mockOnChange = (e: string) => {
    console.log(`mockOnChange called with: ${e}`)
}

const withState = (Story: any, context: any) => {
    const [value, setValue] = useState(context.args.value || '');

    const handleChange = (value: string) => {
        setValue(value);
    };

    return (
        <Story args={{ ...context.args, value, onChange: handleChange }} />
    );
};


const withMaxWidth = (Story: any, context: any) => {
    return (
        <div className='max-w-32'>
            <Story args={context.args} />
        </div>
    )
}

export const Primary: Story = {
    args: {
        dataTestId: "status-select",
        id: "status",
        name: "status",
        value: TaskStatus.TO_DO,
        onChange: mockOnChange,
        options: [
            { value: TaskStatus.TO_DO, label: statusDisplay(TaskStatus.TO_DO) },
            { value: TaskStatus.IN_PROGRESS, label: statusDisplay(TaskStatus.IN_PROGRESS) },
            { value: TaskStatus.DONE, label: statusDisplay(TaskStatus.DONE) },
        ]
    },
    decorators: [withState, withMaxWidth],
}