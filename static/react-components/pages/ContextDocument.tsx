import React, { useEffect, useRef, useState } from 'react';

import MDEditor from '@uiw/react-md-editor';

import { Button } from '#components/reusable/Button';
import { useContextDocument } from '#hooks/useContextDocument';
import { placeholderContextDocument } from '#constants/contextDocumentPlaceholder';
import { ContextDocumentDto } from '#types';

import '#styles/mdeditor.css';
import '#styles/markdown_preview.css';
// Context Document is a document that contains the context of 
// the project. It is used in the context window of the LLM so
// that the LLM can provide more accurate and relevant responses.


const CONTEXT_DOCUMENT_TITLE = 'Context Document';

const ContextDocument = () => {
    const { contextDocument, updateContextDocument, isLoadingContextDocument, errorContextDocument } = useContextDocument();

    const [content, setContent] = useState(contextDocument?.content || '');
    const [isEditing, setIsEditing] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [height, setHeight] = useState(0);

    useEffect(() => {
        if (containerRef.current) {
            setHeight(containerRef.current.clientHeight);
        }
    }, []);

    const handleSaveChanges = () => {
        let updatedContextDocument: ContextDocumentDto;

        if (!contextDocument) {
            updatedContextDocument = {
                title: CONTEXT_DOCUMENT_TITLE,
                content: content,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
        } else {
            updatedContextDocument = {
                id: contextDocument.id,
                title: CONTEXT_DOCUMENT_TITLE,
                content: content,
                created_at: contextDocument.created_at,
                updated_at: new Date().toISOString()
            };
        }

        updateContextDocument(updatedContextDocument)
        setIsEditing(false);
    }

    const handleCancelChanges = () => {
        setContent(contextDocument?.content || '');
        setIsEditing(false);
    }

    const handleEdit = (content: string) => {
        setIsEditing(true);
        setContent(content);
    }

    return (
        <div className="flex-grow flex flex-col justify-between gap-2 pt-10 px-4 overflow-hidden" ref={containerRef}>
            <div className='flex items-center justify-between h-15'>
                <div className='flex flex-col gap-1 items-start max-w-sm'>
                    <h1 className='text-2xl font-bold text-foreground'>{CONTEXT_DOCUMENT_TITLE}</h1>
                    <p className='flex-shrink text-xs text-muted-foreground'>
                        This document is automatically included in your prompts. It should give the
                        model a good overview of your project.
                    </p>
                </div>
                <div className='flex items-center gap-2'>
                    {isEditing && (
                        <>
                            <Button
                                onClick={handleSaveChanges}
                            >
                                Save
                            </Button>
                            <Button
                                onClick={handleCancelChanges}
                            >
                                Cancel
                            </Button>
                        </>
                    )}
                </div>
            </div>
            <div className='flex-grow flex flex-col' >
                <MDEditor
                    value={content}
                    onChange={(value?: string) => handleEdit(value || '')}
                    visibleDragbar={false}
                    overflow={false}
                    height={`${height - 140}px`}
                    preview='edit'
                    fullscreen={false}
                    textareaProps={{
                        className: 'bg-background text-foreground overflow-y-auto flex-grow flex flex-col',
                        placeholder: placeholderContextDocument
                    }}
                    previewOptions={{
                        className: 'bg-background text-foreground',
                    }}
                />
            </div>
        </div>
    )
}

export default ContextDocument;
