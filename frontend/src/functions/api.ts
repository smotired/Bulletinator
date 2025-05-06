/**
 * Functions for interfacing with the backend API
 */
"use server"

import { BadRequest, ApiError } from "@/types";
import { redirect } from "next/navigation";

// Misc
const API_BASE = "http://localhost:8000"
const API_PATHS = { // Important routes on the backend side
    refresh: "/auth/web/refresh", // Refreshing access tokens
}
const APP_PATHS = {
    login: "/login", // Login page
}

// Types
type Headers = { [header: string]: string }
type FormBody = { [key: string]: string }

// Helpers

async function handleResponse<T = void>(response: Response): Promise<T> {
    if (response.status == 204)
        return undefined as T;
    else if (response.ok) 
        return await response.json() as T;
    throw new ApiError(response.status, await response.json() as BadRequest);
}

async function authenticatedFetch<T = void>(fetchFn: () => Promise<Response>): Promise<T> {
    // Make the response
    const response: Response = await fetchFn();
    try {
        return await handleResponse(response);
    }

    // Make sure this is actually an access token expiration
    catch (error) {
        if (!(error instanceof ApiError) || error.code != "invalid_access_token")
            throw error;
    }

    // Refresh if our token expired, or redirect to login page.
    const refresh: Response = await fetch(API_BASE + API_PATHS.refresh, {
        method: "POST",
        credentials: "include",
    });
    if (!refresh.ok)
        return redirect(APP_PATHS.login);

    // If the refresh was successful, retry the request.
    const retried: Response = await fetchFn();
    return await handleResponse<T>(retried);
}

// Unauthenticated functions

export async function get<T = void>(path: string, headers: Headers): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers,
    });
    return await handleResponse<T>(response);
}

export async function post<T = void>(path: string, headers: Headers, body: object): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: "POST",
        body: JSON.stringify(body),
    });
    return await handleResponse<T>(response);
}

export async function put<T = void>(path: string, headers: Headers, body: object): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: "PUT",
        body: JSON.stringify(body),
    });
    return await handleResponse<T>(response);
}

export async function del<T = void>(path: string, headers: Headers): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers,
        method: "DELETE",
    });
    return await handleResponse<T>(response);
}

// Authenticated functions

export async function getAuth<T = void>(path: string, headers: Headers): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers,
        credentials: 'include',
    }));
}

export async function postAuth<T = void>(path: string, headers: Headers, body: object): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: "POST",
        body: JSON.stringify(body),
        credentials: 'include',
    }));
}

export async function putAuth<T = void>(path: string, headers: Headers, body: object): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: "PUT",
        body: JSON.stringify(body),
        credentials: 'include',
    }));
}

export async function delAuth<T = void>(path: string, headers: Headers): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers,
        method: "DELETE",
        credentials: 'include',
    }));
}

// Form functions

export async function postForm<T = void>(path: string, headers: Headers, form: FormBody): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: "POST",
        body: new URLSearchParams(form),
    });
    return await handleResponse<T>(response);
}

export async function putForm<T = void>(path: string, headers: Headers, form: FormBody): Promise<T> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: "PUT",
        body: new URLSearchParams(form),
    });
    return await handleResponse<T>(response);
}

export async function postFormAuth<T = void>(path: string, headers: Headers, form: FormBody): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: "POST",
        body: new URLSearchParams(form),
        credentials: 'include',
    }));
}

export async function putFormAuth<T = void>(path: string, headers: Headers, form: FormBody): Promise<T> {
    return await authenticatedFetch(async () => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: "PUT",
        body: new URLSearchParams(form),
        credentials: 'include',
    }));
}
