/**
 * (Very limited) server component for the board editor page.
 * Fetches initial board object and item contents.
 */

import { getBoard } from "@/functions/boards";
import { getBoardItems } from "@/functions/items";
import { ApiError } from "@/types";
import { notFound, redirect, RedirectType } from "next/navigation";

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
    
    // fallback
    if (!board)
        return <p>board gone</p>

    // Fetch the items (if board fetch was successful this should be too)
    const [ items, itemCookies ] = await getBoardItems(board.id)

    return (
        <p>{username} / {boardId}: {board.name} - {items.metadata.count} items</p>
    )
}