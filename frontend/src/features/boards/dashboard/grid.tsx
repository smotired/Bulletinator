"use client";

import { colorFromString } from "@/app/utils/color";
import AccountAvatar from "@/components/AccountAvatar";
import { BoardIcon } from "@/components/BoardIcon";
import LanguageIcon from '@mui/icons-material/Language';
import LockIcon from '@mui/icons-material/Lock';
import { Account, Board, Collection } from "@/types";
import { Box, Card, Grid, Typography } from "@mui/material";
import Link from "next/link";
import { useState } from "react";

function BoardCard({ board, owner }: { board: Board, owner: Account })
{
    const [ hovered, setHovered ] = useState<boolean>(false);

    return (
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
            <Link title={board.name} href={`/boards/${owner.username}-${board.identifier}`}>
                <Card elevation={hovered ? 12 : 4}
                    onMouseOver={() => setHovered(true)} onMouseOut={() => setHovered(false)}
                    sx={{ display: 'flex', flexDirection: 'row' }} >
                    <Box sx={{ padding: 4, bgcolor: colorFromString(board.name) }}>
                        <BoardIcon color='disabled' type={board.icon} />
                    </Box>

                    <Grid container sx={{ padding: 2, flexGrow: 1 }}>
                        <Grid size={12}>
                            <Typography noWrap variant="h6">{board.name}</Typography>
                        </Grid>
                        <Grid size={12} sx={{ display: 'flex', flexDirection: 'row', gap: '0.5rem', alignItems: 'center' }}>
                            {
                                board.public ?
                                <LanguageIcon color="disabled" sx={{ width: 18, height: 18 }} />
                                :
                                <LockIcon color="disabled" sx={{ width: 18, height: 18 }} />
                            }
                            <AccountAvatar account={owner} sx={{ width: 24, height: 24, fontSize: '0.75rem' }} />
                            <Typography noWrap>{owner.display_name || owner.username}</Typography>
                        </Grid>
                    </Grid>
                </Card>
            </Link>
        </Grid>
    )
}

export default function BoardGrid({ boards, owners }: {
    boards: Collection<Board>,
    owners: { [id: string]: Account },
}) {

    return (
        <Grid container spacing={2} sx={{ mt: 2 }}>
            {
                boards.contents.map((board: Board) => <BoardCard key={board.id} board={board} owner={owners[board.owner_id]} />)
            }
        </Grid>
    )
}