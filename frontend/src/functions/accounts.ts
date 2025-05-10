import { AuthenticatedAccount, CookieSettings } from "@/types";
import { getAuth } from "./api";

/**
 * Gets the currently authenticated account object.
 * @param shouldRedirect If we should redirect upon authentication failure.
 * @returns The account object for the currently authenticated account.
 */
export async function getOwnAccount(shouldRedirect: boolean = true): Promise<[AuthenticatedAccount, CookieSettings | null]> {
    return await getAuth<AuthenticatedAccount>('/accounts/me', {}, false, shouldRedirect);
}