/**
 * Contains the most basic functionality for accessing our API.
 * Client components should not generally use these functions, but should call the server functions
 * exported by other files in the functions module.
 * These server-side functions should call the API functions in this file as tanstack-query functions.
 */
"use server";

import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { ApiError, BadRequest, CookieSettings } from "@/types";

// Basic variables
const API_BASE = "http://localhost:8000"; // Base URL for all requests to the API
const API_PATHS = { // Paths to certain routes on the backend server
    login: "/auth/web/login", // Logging in
    refresh: "/auth/web/refresh", // Refreshing access tokens in cookies.
    logout: "/auth/web/logout", // Logging out
}
const ACCESS_KEY = 'bulletinator_access_token';
const REFRESH_KEY = 'bulletinator_refresh_token';

const APP_PATHS = { // Paths for the frontend application
    login: "/login", // Path to the Login page.
}

// Request-related types

type Headers = { [header: string]: string };
type FormBody = { [key: string]: string, };

// Method to convert an HTTP response body to either the specified object or a BadRequest
async function handleResponse<T = void>(response: Response, forwardCookies: boolean, joinedSettings: CookieSettings | null = null): Promise<[ T, CookieSettings | null ]> {
    // Get the cookie settings to update
    const settings: CookieSettings | null = forwardCookies ? convertCookies(response) : null;
    if (settings && joinedSettings)
        Object.values(joinedSettings).forEach(setting => { settings[setting.key] = setting });

    // Return expected type on a valid response
    if (response.ok) {
        if (response.status == 204)
            return [ undefined as T, settings ];
        return [ await response.json() as T, settings ];
    }

    // Handle an invalid response
    throw new ApiError(response.status, await response.json() as BadRequest);
};

// Makes an HTTP request and tried to convert the response body to the type.
// If it fails because the access token was invalid, tries to refresh the access token.
// If that fails as well, redirects the user to the login page.
// If the refresh is successful, performs the request again.
/**
 * 
 * @param fetchFn The actual fetch function, which takes in an access token and makes the request.
 * @param forwardCookies If we should forward cookie settings from the backend to the response
 * @param shouldRedirect If we should redirect to the login page when failing to refresh the access token
 * @returns 
 */
async function authenticatedFetch<T = void>(fetchFn: (token: string) => Promise<Response>, forwardCookies: boolean, shouldRedirect: boolean) : Promise<[ T, CookieSettings | null ]> {
    // Get the cookies from the request and use them for the fetch
    const cookieStore = await cookies();
    if (!cookieStore.has(ACCESS_KEY)) { // Redirect to login page if not authenticated
        if (shouldRedirect)
            return redirect(APP_PATHS.login);
        throw new ApiError(403, { error: "not_authenticated", message: "Not authenticated", detail: null });
    }
    const accessCookie = cookieStore.get(ACCESS_KEY)!;
    
    // Perform the fetch and return if successful or if the error is anything other than "invalid access token"
    const response: Response = await fetchFn(accessCookie.value);
    try {
        return await handleResponse<T>(response, forwardCookies);
    }
    catch (error) {
        // Re-throw error if it's not an APIError caused by an invalid access token
        if (!(error instanceof ApiError) || error.code != "invalid_access_token")
            throw error;
    }

    // Construct a header for the refresh request
    console.log("Refreshing user access token.");
    if (!cookieStore.has(REFRESH_KEY)) // Redirect to login page if not authenticated
        return redirect(APP_PATHS.login);
    const refreshCookie = cookieStore.get(REFRESH_KEY)!;
    const refreshHeaders = { Cookie: `${REFRESH_KEY}=${refreshCookie.value}` }

    // Try refreshing the access token, redirecting to the login page on failure.
    const refresh: Response = await fetch(API_BASE + API_PATHS.refresh, {
        method: 'POST',
        headers: refreshHeaders,
        credentials: 'include',
    });
    if (!refresh.ok) // Redirect to login page if refresh token is invalid/expired
        return redirect(APP_PATHS.login);
    const newToken = convertCookies(refresh)[ACCESS_KEY];
    
    // If the refresh was successful, retry the request.
    console.log("Retrying user request.");
    const retried: Response = await fetchFn(newToken.value);
    return handleResponse<T>(retried, true, { accessTokenKey: newToken }); // Forcibly forward cookies now, and pass in the updated cookie.
}

/**
 * Asynchronous server function to up date cookies in a request
 * @param settings The cookie updates
 */
export async function updateCookies(settings: CookieSettings) {
    // Ensure dates are added correctly
    Object.keys(settings).forEach((key: string) => {
        if ('expires' in settings[key].options)
            settings[key].options['expires'] = new Date(settings[key].options['expires'] as string);
    });

    // Update the settings
    const cookieStore = await cookies();
    Object.values(settings).forEach(({ key, value, options }) => cookieStore.set(key, value, options));
}

// Method to convert an HTTP Response's newly-set cookies to a dictionary
function convertCookies(response: Response): CookieSettings {
    const responseCookies: CookieSettings = {};
    response.headers.getSetCookie().forEach((setting: string) => {
        const [cookie, ...optionsArr] = setting.split(';').map(s => s.trim().split('='));
        const [key, value] = cookie;
        const options: { [key: string]: string } = {};
        optionsArr.forEach(([ option, data ]: string[]) => { options[option] = data; })
        responseCookies[key] = { key, value, options };
    });
    return responseCookies;
}

// The following functions will send the actual request expecting the generic type as a body in return.

// Unauthenticated Request Functions

export async function get<T = void>(path: string, headers: Headers, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers,
    });
    return await handleResponse<T>(response, forwardCookies);
}

export async function post<T>(path: string, headers: Headers, body: object, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: 'POST',
        body: JSON.stringify(body),
    });
    return await handleResponse<T>(response, forwardCookies);
}

export async function put<T = void>(path: string, headers: Headers, body: object, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
        },
        method: 'PUT',
        body: JSON.stringify(body),
    });
    return await handleResponse<T>(response, forwardCookies);
}

export async function del<T = void>(path: string, headers: Headers, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers,
        method: 'DELETE',
    });
    return await handleResponse<T>(response, forwardCookies);
}

// Authenticated Request Functions

export async function getAuth<T = void>(path: string, headers: Headers, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}

export async function postAuth<T = void>(path: string, headers: Headers, body: object, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        method: 'POST',
        body: JSON.stringify(body),
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}

export async function putAuth<T = void>(path: string, headers: Headers, body: object, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/json',
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        method: 'PUT',
        body: JSON.stringify(body),
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}

export async function delAuth<T = void>(path: string, headers: Headers, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        method: 'DELETE',
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}

// Form Request Functions

export async function postForm<T = void>(path: string, headers: Headers, form: FormBody, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: 'POST',
        body: new URLSearchParams(form),
    });
    return await handleResponse<T>(response, forwardCookies);
}

export async function putForm<T = void>(path: string, headers: Headers, form: FormBody, forwardCookies: boolean = false) : Promise<[ T, CookieSettings | null ]> {
    const response: Response = await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method: 'PUT',
        body: new URLSearchParams(form),
    });
    return await handleResponse<T>(response, forwardCookies);
}

export async function postFormAuth<T = void>(path: string, headers: Headers, form: FormBody, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        method: 'POST',
        body: new URLSearchParams(form),
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}

export async function putFormAuth<T = void>(path: string, headers: Headers, form: FormBody, forwardCookies: boolean = false, shouldRedirect: boolean = true) : Promise<[ T, CookieSettings | null ]> {
    return await authenticatedFetch<T>(async (token: string) => await fetch(API_BASE + path, {
        headers: {
            ...headers,
            'Content-Type': 'application/x-www-form-urlencoded',
            Cookie: `${ACCESS_KEY}=${token}`,
            credentials: 'include',
        },
        method: 'PUT',
        body: new URLSearchParams(form),
        credentials: 'include',
    }), forwardCookies, shouldRedirect);
}