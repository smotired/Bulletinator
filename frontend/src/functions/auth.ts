import { CookieSettings } from "@/types";
import { postFormAuth } from "./api";

export async function login(
    form: { identifier: string, password: string },
): Promise<[void, CookieSettings | null]> {
    return await postFormAuth('/auth/web/login', {}, form, true)
}