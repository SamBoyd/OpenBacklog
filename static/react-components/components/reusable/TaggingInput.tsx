import React from 'react';
import TagsInput from 'react-tagsinput';

import 'react-tagsinput/react-tagsinput.css';

import '../../styles/tagging_input.css';

// Docs for TagsInput: https://github.com/olahol/react-tagsinput

type TaggingInputProps = {
    initialTags: string[];
    onChange: (tags: string[]) => void;
};

const TaggingInput = ({ initialTags, onChange }: TaggingInputProps) => {
    const [tags, setTags] = React.useState(initialTags);

    React.useEffect(() => {
        const filteredValue = initialTags.filter((tag) => tag !== '');
        setTags(filteredValue);
    }, []);

    const handleChange = (value: string[]) => {
        const filteredValue = value.filter((tag) => tag !== '');
        setTags(filteredValue);
        onChange(filteredValue);
    };

    return (
        <div data-testid='tagging-input'>
            <TagsInput value={tags} onChange={handleChange} />
        </div>
    );
};

export default TaggingInput;
