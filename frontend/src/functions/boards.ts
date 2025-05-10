/**
 * Server actions for board-related functionality
 */

import { Board, Collection, CookieSettings } from "@/types";
import { getAuth, postAuth } from "./api";

export async function getEditableBoards(): Promise<[Collection<Board>, CookieSettings | null]> {
    return await getAuth<Collection<Board>>('/boards/editable', {});
}

export async function createBoard(body: { name: string, identifier: string, icon: string, public: boolean }): Promise<[Board, CookieSettings | null]> {
    return await postAuth<Board>('/boards', {}, body);
}