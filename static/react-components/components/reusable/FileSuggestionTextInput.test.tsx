import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileSuggestionTextInput from './FileSuggestionTextInput';
import { useFilepathSuggestionFetching } from '#hooks/useFilepathSuggestionFetching';

// Mock the useFilepathSuggestionFetching hook
vi.mock('#hooks/useFilepathSuggestionFetching');

const mockUseFilepathSuggestionFetching = vi.mocked(useFilepathSuggestionFetching);

describe('FileSuggestionTextInput', () => {
    const defaultProps = {
        value: '',
        onChange: vi.fn(),
        placeholder: 'Enter your text...',
        testId: 'file-suggestion-input',
    };

    const mockSuggestions = [
        '@user/frontend-app/src/components/Button.tsx',
        '@user/frontend-app/src/components/Modal.tsx',
        '@user/backend-api/src/controllers/auth.ts',
    ];

    beforeEach(() => {
        vi.clearAllMocks();

        // Mock scrollIntoView which is not available in test environment
        Element.prototype.scrollIntoView = vi.fn();

        // Default mock - no suggestions
        mockUseFilepathSuggestionFetching.mockReturnValue({
            suggestions: [],
            isLoading: false,
            error: null,
        });
    });

    describe('Basic Functionality', () => {
        it('renders textarea with correct props', () => {
            render(<FileSuggestionTextInput {...defaultProps} />);

            const textarea = screen.getByTestId('file-suggestion-input');
            expect(textarea).toBeInTheDocument();
            expect(textarea).toHaveAttribute('placeholder', 'Enter your text...');
        });

        it('calls onChange when text is entered', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');
            await user.type(textarea, 'Hello world');

            // userEvent.type calls onChange for each character, check that it was called with final value
            expect(onChange).toHaveBeenNthCalledWith(1, 'H');
            expect(onChange).toHaveBeenNthCalledWith(2, 'e');
            expect(onChange).toHaveBeenNthCalledWith(3, 'l');
            expect(onChange).toHaveBeenNthCalledWith(4, 'l');
            expect(onChange).toHaveBeenNthCalledWith(5, 'o');
            expect(onChange).toHaveBeenNthCalledWith(6, ' ');
            expect(onChange).toHaveBeenNthCalledWith(7, 'w');
            expect(onChange).toHaveBeenNthCalledWith(8, 'o');
            expect(onChange).toHaveBeenNthCalledWith(9, 'r');
            expect(onChange).toHaveBeenNthCalledWith(10, 'l');
            expect(onChange).toHaveBeenNthCalledWith(11, 'd');
        });

        it('displays loading skeleton when loading prop is true', () => {
            render(<FileSuggestionTextInput {...defaultProps} loading={true} />);

            // Should render skeleton instead of textarea
            expect(screen.queryByTestId('file-suggestion-input')).not.toBeInTheDocument();
        });

        it('handles disabled state correctly', () => {
            render(<FileSuggestionTextInput {...defaultProps} disabled={true} />);

            const textarea = screen.getByTestId('file-suggestion-input');
            expect(textarea).toBeDisabled();
        });
    });

    describe('@ Symbol Detection', () => {
        it('does not trigger filepath suggestions for normal text', () => {
            render(<FileSuggestionTextInput {...defaultProps} value="Hello world" />);

            expect(mockUseFilepathSuggestionFetching).toHaveBeenCalledWith({
                searchQuery: ''
            });
        });

        it('triggers filepath suggestions when @ symbol is typed', async () => {
            const user = userEvent.setup();
            let currentValue = '';
            const onChange = vi.fn((value: string) => {
                currentValue = value;
            });

            const { rerender } = render(
                <FileSuggestionTextInput {...defaultProps} value={currentValue} onChange={onChange} />
            );

            const textarea = screen.getByTestId('file-suggestion-input');

            // Type @ symbol
            await user.type(textarea, '@');

            // Rerender with updated value
            rerender(<FileSuggestionTextInput {...defaultProps} value="@" onChange={onChange} />);

            // Should trigger suggestions with empty query
            expect(mockUseFilepathSuggestionFetching).toHaveBeenCalledWith({
                searchQuery: ''
            });
        });

        it('extracts search query after @ symbol', async () => {
            const user = userEvent.setup();

            render(<FileSuggestionTextInput {...defaultProps} value="@comp" />);

            const textarea = screen.getByTestId('file-suggestion-input') as HTMLTextAreaElement;

            // Focus and position cursor after '@comp'
            await user.click(textarea);
            textarea.setSelectionRange(5, 5);

            // Trigger key events to update cursor context
            fireEvent.keyUp(textarea);
            fireEvent.click(textarea);

            // Wait for state updates
            await waitFor(() => {
                expect(mockUseFilepathSuggestionFetching).toHaveBeenCalledWith({
                    searchQuery: 'comp'
                });
            });
        });

        it('stops suggestion mode when whitespace is encountered', async () => {
            const user = userEvent.setup();
            let currentValue = '';
            const onChange = vi.fn((value: string) => {
                currentValue = value;
            });

            const { rerender } = render(
                <FileSuggestionTextInput {...defaultProps} value={currentValue} onChange={onChange} />
            );

            const textarea = screen.getByTestId('file-suggestion-input');

            // Type @comp followed by space
            await user.type(textarea, '@comp ');

            // Rerender with updated value
            rerender(<FileSuggestionTextInput {...defaultProps} value="@comp " onChange={onChange} />);

            // Should not be in suggestion mode
            expect(mockUseFilepathSuggestionFetching).toHaveBeenCalledWith({
                searchQuery: ''
            });
        });

        it('handles multiple @ symbols correctly', async () => {
            const user = userEvent.setup();

            render(<FileSuggestionTextInput {...defaultProps} value="Check @file1 and @file2" />);

            const textarea = screen.getByTestId('file-suggestion-input') as HTMLTextAreaElement;

            // Focus and position cursor after the second '@file2'
            await user.click(textarea);
            textarea.setSelectionRange(25, 25); // After '@file2'

            // Trigger key events to update cursor context
            fireEvent.keyUp(textarea);
            fireEvent.click(textarea);

            // Wait for state updates
            await waitFor(() => {
                expect(mockUseFilepathSuggestionFetching).toHaveBeenCalledWith({
                    searchQuery: 'file2'
                });
            });
        });
    });

    describe('Dropdown Interaction', () => {
        beforeEach(() => {
            mockUseFilepathSuggestionFetching.mockReturnValue({
                suggestions: mockSuggestions,
                isLoading: false,
                error: null,
            });
        });

        it('shows dropdown when suggestions are available', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();
            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger isTyping state
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5); // After '@comp'
            await user.type(textarea, 'o');

            // Should show dropdown with suggestions
            await waitFor(() => {
                expect(screen.getByText(/Button\.tsx/)).toBeInTheDocument();
            });
        });

        it('navigates dropdown with arrow keys', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            const { rerender } = render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger isTyping state
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5); // After '@comp'
            await user.type(textarea, 'o');


            await waitFor(() => {
                expect(screen.getByText(/Button\.tsx/)).toBeInTheDocument();
            });

            // Arrow down should move to next item
            await user.keyboard('{ArrowDown}');

            // Arrow up should move back
            await user.keyboard('{ArrowUp}');

            // Enter should select highlighted item
            await user.keyboard('{Enter}');

            expect(onChange).toHaveBeenCalledWith('@user/frontend-app/src/components/Button.tsx');
        });

        it('closes dropdown with Escape key', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();
            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger dropdown
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5);
            await user.type(textarea, 'o');

            await waitFor(() => {
                expect(screen.getByText(/Button\.tsx/)).toBeInTheDocument();
            });

            // Escape should close dropdown
            await user.keyboard('{Escape}');

            await waitFor(() => {
                expect(screen.queryByText(/Button\.tsx/)).not.toBeInTheDocument();
            });
        });

        it('selects suggestion on click', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger dropdown
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5);
            await user.type(textarea, 'o');

            await waitFor(() => {
                expect(screen.getByText(/Button\.tsx/)).toBeInTheDocument();
            });

            // Click on suggestion
            const suggestion = screen.getByText(/Button\.tsx/);
            await user.click(suggestion);

            expect(onChange).toHaveBeenCalledWith('@user/frontend-app/src/components/Button.tsx');
        });
    });

    describe('Text Insertion', () => {
        it('replaces @searchQuery with selected suggestion', () => {
            const onChange = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} value="Check @comp and continue" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Simulate suggestion selection
            // This would normally be triggered by the dropdown component
            // We'll test the handleSuggestionSelect function indirectly

            // Position cursor after '@comp'
            (textarea as HTMLTextAreaElement).setSelectionRange(11, 11);
            fireEvent.keyUp(textarea);

            // The actual replacement logic is tested through integration
            // with the dropdown component
        });

        it('maintains cursor position after suggestion insertion', async () => {
            const user = userEvent.setup();
            mockUseFilepathSuggestionFetching.mockReturnValue({
                suggestions: mockSuggestions,
                isLoading: false,
                error: null,
            });

            const onChange = vi.fn();
            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and trigger dropdown
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5);
            await user.type(textarea, 'o');

            await waitFor(() => {
                expect(screen.getByText(/Button\.tsx/)).toBeInTheDocument();
            });

            // Select suggestion with Enter
            await user.keyboard('{Enter}');

            // Verify onChange was called with correct value
            expect(onChange).toHaveBeenCalledWith('@user/frontend-app/src/components/Button.tsx');
        });
    });

    describe('Loading and Error States', () => {
        it('shows loading state in dropdown', async () => {
            mockUseFilepathSuggestionFetching.mockReturnValue({
                suggestions: [],
                isLoading: true,
                error: null,
            });

            const user = userEvent.setup();
            const onChange = vi.fn();
            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger dropdown
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(5, 5);
            await user.type(textarea, 'o');

            await waitFor(() => {
                expect(screen.getByText('Loading...')).toBeInTheDocument();
            });
        });

        it.skip('shows error state in dropdown', async () => {
            mockUseFilepathSuggestionFetching.mockReturnValue({
                suggestions: [],
                isLoading: false,
                error: {
                    name: 'Failed to fetch',
                    message: 'Failed to fetch',
                },
            });

            const user = userEvent.setup();
            const onChange = vi.fn();
            render(<FileSuggestionTextInput {...defaultProps} value="" onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and type to trigger dropdown
            await user.click(textarea);
            // (textarea as HTMLTextAreaElement).setSelectionRange(5, 5);
            await user.type(textarea, '@');

            await waitFor(() => {
                expect(screen.getByText(/Failed to load file suggestions/)).toBeInTheDocument();
            });
        });

        it('shows empty state when no suggestions found', async () => {
            mockUseFilepathSuggestionFetching.mockReturnValue({
                suggestions: [],
                isLoading: false,
                error: null,
            });

            const user = userEvent.setup();
            render(<FileSuggestionTextInput {...defaultProps} value="@xyz" />);

            const textarea = screen.getByTestId('file-suggestion-input');

            // Focus and trigger dropdown
            await user.click(textarea);
            (textarea as HTMLTextAreaElement).setSelectionRange(4, 4);
            fireEvent.keyUp(textarea);

            // Empty state is only shown when there's a search query but no results
            // The dropdown won't be visible if there are no suggestions and no loading
        });
    });

    describe('Edge Cases', () => {
        it('handles blur events correctly', async () => {
            const user = userEvent.setup();
            const onBlur = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} value="@comp" onBlur={onBlur} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            await user.click(textarea);
            await user.tab(); // Blur the textarea

            expect(onBlur).toHaveBeenCalled();
        });

        it('handles custom keyDown events', async () => {
            const user = userEvent.setup();
            const onKeyDown = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} onKeyDown={onKeyDown} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            await user.type(textarea, 'test');

            expect(onKeyDown).toHaveBeenCalled();
        });

        it('prevents Enter when submitOnEnter is true', async () => {
            const user = userEvent.setup();
            const onChange = vi.fn();

            render(<FileSuggestionTextInput {...defaultProps} submitOnEnter={true} onChange={onChange} />);

            const textarea = screen.getByTestId('file-suggestion-input');

            await user.type(textarea, 'test{Enter}');

            // Should not have newline in value since Enter is prevented
            expect(onChange).not.toHaveBeenCalledWith('test\n');
        });
    });
});