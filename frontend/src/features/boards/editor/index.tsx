/**
 * (Very limited) server component for the board editor page.
 * Fetches initial board object and item contents.
 */
"use server";

import CookieSetter from "@/components/CookieSetter";
import { getBoard } from "@/functions/boards";
import { getBoardItems } from "@/functions/items";
import { ApiError } from "@/types";
import { notFound, redirect, RedirectType } from "next/navigation";
import EditorTopMenu from "./topmenu";

export default async function BoardEditor({ slug }: { slug: string }) {
    // Convert slug into username and board identifier
    const [ username, boardId ] = slug.split('-');
    // Fetch the board
    const [ board, boardCookies ] = await getBoard(slug)
        .catch((error: Error) => {
            // We return a 404 if this board is not found/private, or (for now) redirect to the root otherwise
            if (error instanceof ApiError && error.status == 404)
                notFound();
            redirect('/', RedirectType.push);
        }) || [ undefined, undefined ] // fallback that should never hit;
    
    // fallback (again, should never hit)
    if (!board) redirect('/', RedirectType.push);

    // Fetch the items (if board fetch was successful this should be too)
    const [ items, itemCookies ] = await getBoardItems(board.id)

    return (
        <>
            <CookieSetter settings={boardCookies} />
            <CookieSetter settings={itemCookies} />

            <EditorTopMenu board={board} />
        </>
    )
}