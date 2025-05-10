/**
 * Server actions for board-related functionality
 */

import { Board, Collection, CookieSettings } from "@/types";
import { getAuth } from "./api";

export async function getEditableBoards(): Promise<[Collection<Board>, CookieSettings | null]> {
    return await getAuth<Collection<Board>>('/boards/editable', {});
}