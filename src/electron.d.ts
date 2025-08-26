// This allows TypeScript to recognize the 'electronAPI' object on the window
export interface IElectronAPI {
    openExternal: (url: string) => void;
}

declare global {
    interface Window {
        electronAPI: IElectronAPI;
    }
}
