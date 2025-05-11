import { CookiePromise } from "@/types";
import { postAuth, postForm } from "./api";

export async function login(
    form: { identifier: string, password: string },
): CookiePromise {
    return await postForm('/auth/web/login', {}, form, true);
}

export async function logout(): CookiePromise {
    return await postAuth('/auth/web/logout', {}, {}, true);
}