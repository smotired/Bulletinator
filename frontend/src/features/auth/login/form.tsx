"use client";
import { useAuth } from "@/contexts/auth";
import call from "@/functions";
import { login } from "@/functions/auth";
import { Stack, TextField, Button, Alert } from "@mui/material";
import { useRouter, useSearchParams } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";

type Login = { identifier: string, password: string }

export default function LoginFormClient() {
    const router = useRouter();
    const nextPath = useSearchParams().get('next');
    const { handleLogin, authenticated } = useAuth();

    const [ hasAttempted, setHasAttempted ] = useState<boolean>(false);
    const [ disabled, setDisabled ] = useState<boolean>(true);
    const [ form, setForm ] = useState<Login | null>(null);
    const [ error, setError ] = useState<string | null>(null);

    const identifierRef = useRef<HTMLInputElement>(null);
    const passwordRef = useRef<HTMLInputElement>(null);

    function handleInputChange(event: ChangeEvent) {
        const identifier = identifierRef.current?.value ?? "";
        const password = passwordRef.current?.value ?? "";
        if (form == null) setDisabled(identifier == "" || password == "");
    }

    function handleSubmit(event: FormEvent) {
        event.preventDefault();
        
        // Check submission
        const identifier = identifierRef.current?.value ?? "";
        const password = passwordRef.current?.value ?? "";
        if (disabled || identifier == "" || password == "") return;

        // Tell state to perform login with useEffect
        setHasAttempted(true);
        setError(null);
        setDisabled(true);
        console.log(JSON.stringify({ identifier, password }))
        setForm({ identifier, password })
    }

    useEffect(() => {
        // If the form is being reset, focus the appropriate field and skip.
        if (form == null) {
            if (hasAttempted)
                passwordRef.current && passwordRef.current.focus();
            else 
                identifierRef.current && identifierRef.current.focus();
            return;
        }

        // Otherwise, send the login request.
        call(login, form)
            .then(() => {
                handleLogin();
            })
            .catch((error: Error) => {
                setForm(null);
                setError(error.message);
                if (passwordRef.current)
                    passwordRef.current.value = '';
            })
    }, [form]);

    // If authenticated, immediately go to Next
    useEffect(() => { authenticated && router.push(nextPath || '/dashboard'); }, [authenticated]);

    return (
        <form onSubmit={handleSubmit} className="flex flex-col w-full gap-4 items-stretch">
            {/* Fields */}
            <TextField inputRef={identifierRef} onChange={handleInputChange} label="Email or Username" />
            <TextField inputRef={passwordRef} onChange={handleInputChange} label="Password" type="password" />

            {/* Login button */}
            <Button loading={form != null} variant='contained' type='submit' disabled={disabled} sx={{ p: 1 }}>
                Log In
            </Button>

            {/* Error message */}
            { error && <Alert severity="error">{error}</Alert> }
        </form>
    )
}