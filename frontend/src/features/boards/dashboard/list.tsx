import { Board, Collection } from "@/types";
import { Card, Stack, Typography } from "@mui/material";


export default function BoardList({ boards }: { boards: Collection<Board> }) {
    return (
        <Stack spacing={2}>
            {
                boards.contents.map((board: Board) =>
                    <Card key={board.id}>
                        <Typography>{board.name}</Typography>
                    </Card>
                )
            }
        </Stack>
    )
}