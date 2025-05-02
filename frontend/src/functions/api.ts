import { redirect } from "next/navigation";

const BASE_URL = "http://localhost:8000";
const API_PATHS = {
    refresh: "/auth/web/refresh",
    login: "/auth/web/login",
};
const APP_PATHS = {
    login: "/login",
}

type ErrorResponse = {
    error: string,
    message: string,
    detail: object | null,
}

type FormBody = { [key: string]: string }

class ApiError extends Error {
    status: number;
    code: string;
    /**
     * Error object containing response status, error code, and error message
     */
    constructor(status: number, { error, message }: { error: string, message: string }) {
      super(message);
      this.status = status;
      this.code = error;
    }
}

const handleResponse = async (response: Response) => {
    if (response.ok) {
        return response.status == 204 ? {} : await response.json();
    } else {
        const error: ErrorResponse = await response.json() as ErrorResponse;
        if (error.detail) {
            throw new ApiError(response.status, {
                error: "validation",
                message: JSON.stringify(error.detail),
            });
        } else {
            throw new ApiError(response.status, error);
        }
    }
};

// Functions for unauthenticated routes

const get = async (url: string, headers: Headers) => {
    const response = await fetch(BASE_URL + url, {
        headers,
    });
    return await handleResponse(response);
};

const put = async (url: string, headers: Headers, data: object) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/json",
        },
        method: "PUT",
        body: JSON.stringify(data),
    });
    return await handleResponse(response);
};

const post = async (url: string, headers: Headers, data: object) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify(data),
    });
    return await handleResponse(response);
};

const del = async (url: string, headers: Headers) => {
    const response = await fetch(BASE_URL + url, {
        headers,
        method: "DELETE",
    });
    return await handleResponse(response);
};

// Functions for authenticated routes

const refreshOrRedirect = async () => {
    const response = await fetch (BASE_URL + API_PATHS.refresh, {
        method: "POST",
        credentials: "include",
    });
    try {
        await handleResponse(response); // don't return anything on success, we have refreshed
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_refresh_token")
            throw error;

        // Redirect to login screen
        redirect(APP_PATHS.login);
    }
}

const getAuth = async (url: string, headers: Headers) => {
    const response = await fetch(BASE_URL + url, {
        headers,
        credentials: "include",
    });
    try {
        return await handleResponse(response);
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_access_token")
            throw error;

        // Try refreshing access token
        refreshOrRedirect();

        // Retry the request
        const response = await fetch(BASE_URL + url, {
            headers,
            credentials: "include",
        });
        return await handleResponse(response);
    }
};

const putAuth = async (url: string, headers: Headers, data: object) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/json",
        },
        method: "PUT",
        body: JSON.stringify(data),
        credentials: "include",
    });
    try {
        return await handleResponse(response);
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_access_token")
            throw error;

        // Try refreshing access token
        refreshOrRedirect();

        // Retry the request
        const response = await fetch(BASE_URL + url, {
            headers: {
            ...headers,
            "Content-Type": "application/json",
            },
            method: "PUT",
            body: JSON.stringify(data),
            credentials: "include",
        });
        return await handleResponse(response);
    }
};

const postAuth = async (url: string, headers: Headers, data: object) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/json",
        },
        method: "POST",
        body: JSON.stringify(data),
        credentials: "include",
    });
    try {
        return await handleResponse(response);
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_access_token")
            throw error;

        // Try refreshing access token
        refreshOrRedirect();

        // Retry the request
        const response = await fetch(BASE_URL + url, {
            headers: {
            ...headers,
            "Content-Type": "application/json",
            },
            method: "POST",
            body: JSON.stringify(data),
            credentials: "include",
        });
        return await handleResponse(response);
    }
};

const delAuth = async (url: string, headers: Headers) => {
    const response = await fetch(BASE_URL + url, {
        headers,
        method: "DELETE",
        credentials: "include",
    });
    try {
        return await handleResponse(response);
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_access_token")
            throw error;

        // Try refreshing access token
        refreshOrRedirect();

        // Retry the request
        const response = await fetch(BASE_URL + url, {
            headers,
            method: "DELETE",
            credentials: "include",
        });
        return await handleResponse(response);
    }
};

// Functions for form routes

const putForm = async (url: string, headers: Headers, data: FormBody) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/x-www-form-urlencoded",
        },
        method: "PUT",
        body: new URLSearchParams(data),
    });
    return await handleResponse(response);
};

const putFormAuth = async (url: string, headers: Headers, data: FormBody) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/x-www-form-urlencoded",
        },
        method: "PUT",
        body: new URLSearchParams(data),
        credentials: "include",
    });
    try {
        return await handleResponse(response);
    }
    catch (error: unknown) {
        // If this isn't just because access token expired, re-throw error
        if (!(error instanceof ApiError))
            throw error;
        if (error.code != "invalid_access_token")
            throw error;

        // Try refreshing access token
        refreshOrRedirect();

        // Retry the request
        const response = await fetch(BASE_URL + url, {
            headers: {
            ...headers,
            "Content-Type": "application/x-www-form-urlencoded",
            },
            method: "PUT",
            body: new URLSearchParams(data),
            credentials: "include",
        });
        return await handleResponse(response);
    }
};

const postForm = async (url: string, headers: Headers, data: FormBody) => {
    const response = await fetch(BASE_URL + url, {
        headers: {
        ...headers,
        "Content-Type": "application/x-www-form-urlencoded",
        },
        method: "POST",
        body: new URLSearchParams(data),
    });
    return await handleResponse(response);
};

export default { get, post, put, del, getAuth, postAuth, putAuth, delAuth, putForm, putFormAuth, postForm };