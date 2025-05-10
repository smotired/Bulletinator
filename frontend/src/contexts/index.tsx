/**
 * Wrapper for context module. Also contains a wrapper for contects providers that should wrap the whole application.
 */
"use client";
export { useAuth, AuthContextProvider } from './auth';

import { AuthContextProvider } from './auth';

export default function ContextProviders({ children }: { children: React.ReactNode }) {
    return (
        <AuthContextProvider>
            {children}
        </AuthContextProvider>
    )
}