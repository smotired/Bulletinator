"use server";
import { Account, AuthenticatedAccount, Collection, CookiePromise, nullAccount } from "@/types";
import { get, getAuth } from "./api";

/**
 * Gets the currently authenticated account object.
 * @param shouldRedirect If we should redirect upon authentication failure.
 * @returns The account object for the currently authenticated account.
 */
export async function getOwnAccount(shouldRedirect: boolean = true): CookiePromise<AuthenticatedAccount> {
    return await getAuth<AuthenticatedAccount>('/accounts/me', {}, false, shouldRedirect);
}

let accountCache: { [id: string]: Account } = {};
let lastLookupTime: number = 0;

async function refreshAccounts(): Promise<void> {
    const [ collection, _ ] = await get<Collection<Account>>('/accounts', {}, false);
    accountCache = Object.fromEntries(collection.contents.map((a: Account) => [ a.id, a ]));
    lastLookupTime = Date.now();
}

/**
 * Gets the account with an ID from the server-side cache.
 * @param id The ID of the account to look for.
 * @returns The Account object with this ID, or null if no account does.
 */
export async function accountLookup(id: string): Promise<Account> {
    // If it's been longer than 5 minutes, or this account isn't found, force a refresh.
    if (Date.now() - lastLookupTime >= 5000 || !Object.hasOwn(accountCache, id))
        await refreshAccounts();

    return accountCache[id] || nullAccount;
}

/**
 * Gets the accounts with these IDs from the server-side cache.
 * @param ids The IDs of the accounts to look for.
 * @returns The Account objects with these ID, or null if no account does.
 */
export async function multiAccountLookup(ids: string[]): Promise<{ [id: string]: Account }> {
    // If it's been longer than 5 minutes, or any account isn't found, force a refresh.
    if (Date.now() - lastLookupTime >= 5000 || !ids.every((id) => Object.hasOwn(accountCache, id)))
        await refreshAccounts();

    return Object.fromEntries(ids.map(id => [ id, accountCache[id] || nullAccount ]));
}