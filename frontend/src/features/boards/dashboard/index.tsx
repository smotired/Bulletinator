import CookieSetter from "@/components/CookieSetter";
import { getEditableBoards } from "@/functions/boards";
import BoardGrid from "./grid";
import { Container, Divider, Stack, Typography } from "@mui/material";
import { multiAccountLookup } from "@/functions/accounts";
import BoardCreator from "./creator";

export default async function Dashboard() {
    const [ boards, cookies ] = await getEditableBoards();
    const owners = await multiAccountLookup(boards.contents.map(board => board.owner_id))

    return (
        <>
            <CookieSetter settings={cookies} />
            <Container maxWidth='xl' sx={{ mt: 4 }}>
                <Stack direction='row' alignItems='center'>
                    <Typography color="primary" variant="h4" sx={{ flexGrow: 1 }}>Boards</Typography>
                    <BoardCreator />
                </Stack>
                <Divider />

                <BoardGrid boards={boards} owners={owners} />
            </Container>
        </>
    )
}