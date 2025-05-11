/**
 * Server actions for board-related functionality
 */

import { Board, Collection, CookiePromise } from "@/types";
import { getAuth, postAuth } from "./api";

export async function getEditableBoards(): CookiePromise<Collection<Board>> {
    return await getAuth<Collection<Board>>('/boards/editable', {});
}

export async function createBoard(body: { name: string, identifier: string, icon: string, public: boolean }): CookiePromise<Board> {
    return await postAuth<Board>('/boards', {}, body);
}

export async function getBoard(slug: string): CookiePromise<Board> {
    return await getAuth<Board>(`/boards/${slug}`, {})
}