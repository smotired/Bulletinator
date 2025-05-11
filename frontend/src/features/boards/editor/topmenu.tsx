/**
 * Controls for navigation and board settings
 */
"use client";

import { Board } from "@/types";
import { IconButton, Paper, Stack, Tooltip, Typography } from "@mui/material";
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import SettingsIcon from '@mui/icons-material/Settings';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

export default function EditorTopMenu({ board }: { board: Board }) {
    return (
        <Paper elevation={4} sx={{ borderRadius: 0 }}>
            <Stack direction='row' alignItems='center' sx={{ p: 1 }}>
                {/* Breadcrumbs and title */}
                <Typography variant="body1">Boards <ArrowForwardIosIcon sx={{ height: '1rem' }} /> OtherBoard <ArrowForwardIosIcon sx={{ height: '1rem' }} /> </Typography>
                <Typography noWrap variant="h4" sx={{ flexGrow: 1 }}>{board.name}</Typography>

                {/* Control buttons */}
                <Tooltip title='Sharing'>
                    <IconButton><GroupAddIcon /></IconButton>
                </Tooltip>
                <Tooltip title='Board Settings'>
                    <IconButton><SettingsIcon /></IconButton>
                </Tooltip>
            </Stack>
        </Paper>
    )
}