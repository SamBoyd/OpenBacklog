import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { getContextDocument, updateContextDocument } from '#api/contextDocument';
import { ContextDocumentDto } from '#types';


export interface UseContextDocumentReturn {
    contextDocument: ContextDocumentDto | null;
    updateContextDocument: (contextDocument: ContextDocumentDto) => void;
    isLoadingContextDocument: boolean;
    errorContextDocument: Error | null;
}

export const useContextDocument = (): UseContextDocumentReturn => {
    const queryClient = useQueryClient();

    const { 
        data: contextDocument, 
        isLoading: isLoadingContextDocument, 
        error: errorContextDocument 
    } = useQuery<ContextDocumentDto>({
        queryKey: ['contextDocument'],
        queryFn: getContextDocument,
    });

    const updateContextDocumentMutation = useMutation<ContextDocumentDto, Error, ContextDocumentDto>({
        mutationFn: updateContextDocument,
        onSuccess: (data) => {
            queryClient.setQueryData<ContextDocumentDto>(['contextDocument'], data);
        },
        onError: (error) => {
            console.error('[useContextDocument] updateContextDocumentMutation.onError', error);
        },
    });

    return {
        contextDocument: contextDocument || null,
        updateContextDocument: updateContextDocumentMutation.mutate,
        isLoadingContextDocument,
        errorContextDocument,
    };
}
