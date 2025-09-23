export declare const jsonToText: (json: string) => string;
export declare const textToJson: (text: string) => string;
export declare const validateMarkdown: (text: string) => {
    success: boolean;
    error: string | null;
};
