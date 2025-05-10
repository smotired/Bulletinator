import { CookieSettings } from "@/types";
import { postAuth, postForm } from "./api";

export async function login(
    form: { identifier: string, password: string },
): Promise<[void, CookieSettings | null]> {
    return await postForm('/auth/web/login', {}, form, true);
}

export async function logout(): Promise<[void, CookieSettings | null]> {
    return await postAuth('/auth/web/logout', {}, {}, true);
}