import { CookiePromise } from "@/types";
import { updateCookies } from "./api";

export default async function call<T, A extends unknown[]>(
    func: (...args: A) => CookiePromise<T>,
    ...args: A
): Promise<T> {
    const [ result, cookies ] = await func(...args);
    cookies && updateCookies(cookies);
    return result;
}