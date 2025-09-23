// static/react-components/components/reusable/Modal.tsx
import React from 'react';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
}

const Modal = ({ isOpen, onClose, children }: ModalProps) => {
    if (!isOpen) {
        return null;
    }

    interface ModalHandleCloseEvent extends React.MouseEvent<HTMLDivElement, MouseEvent> { }

    const handleClose = (e: ModalHandleCloseEvent): void => {
        e.preventDefault();
        onClose();
    }

    return (
        <div
            id="modal_background"
            data-testid="modal-background"
            onClick={handleClose}
            className="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 overflow-y-scroll flex flex-row justify-center"
        >
            <div
                id="modal_content"
                data-testid="modal-content"
                className="rounded-lg my-12 h-auto sm:w-auto md:max-w-2/3 lg:max-w-2/3 xl:max-w-1/2 flex justify-center items-center"
                onClick={(e) => e.stopPropagation()}
            >
                {children}
            </div>
        </div>
    );
};

export default Modal;
