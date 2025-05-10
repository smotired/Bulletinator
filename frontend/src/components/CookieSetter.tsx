/**
 * Client component that just sets cookies upon rendering.
 */
"use client";
import { CookieSettings } from "@/types";
import { updateCookies } from "@/functions/api";
import { useEffect } from "react";

export default function CookieSetter({ settings }: { settings: CookieSettings | null }) {
    // Set the cookies upon loading
    useEffect(() => { settings && updateCookies(settings).then(); }, []);

    // Return empty fragment
    return <></>;
}