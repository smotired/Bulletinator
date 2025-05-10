/**
 * Provides context for a full application
 */
"use client";
import call from "@/functions";
import { getOwnAccount } from "@/functions/accounts";
import { ApiError, AuthenticatedAccount } from "@/types"
import { createContext, useContext, useEffect, useState } from "react"

export type AuthContextType = {
    loading: boolean,
    authenticated: boolean,
    account: AuthenticatedAccount | null,
    handleLogin: () => void,
    handleLogout: () => void,
}

const AuthContext = createContext<AuthContextType>({
    loading: false,
    authenticated: false,
    account: null,
    handleLogin: () => {},
    handleLogout: () => {},
})

export function AuthContextProvider({ children }: { children: React.ReactNode }) {
    const [ loading, setLoading ] = useState<boolean>(true);
    const [ account, setAccount ] = useState<AuthenticatedAccount | null>(null);
    
    // Refresh authenticated user account when loading is set to true
    useEffect(() => {
        if (!loading) return;
        call(getOwnAccount, false)
            .then((fetched: AuthenticatedAccount) => {
                setAccount(fetched);
                setLoading(false);
            }).catch(() => {
                setAccount(null);
                setLoading(false);
            });
    }, [loading]);

    const handleLogin = () => setLoading(true);
    const handleLogout = () => setAccount(null);

    return (
        <AuthContext.Provider value={{ loading, authenticated: account != null, account, handleLogin, handleLogout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext);