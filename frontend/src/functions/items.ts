/**
 * Server actions for item-related functionality
 */
"use server";

import { Item, Collection, CookiePromise } from "@/types";
import { getAuth } from "./api";

export async function getBoardItems(boardId: string): CookiePromise<Collection<Item>> {
    return await getAuth<Collection<Item>>(`/boards/${boardId}/items`, {})
}