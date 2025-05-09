/**
 * Client component for the navigation bar.
 */
"use client";

import { appbarGradient } from "@/theme";
import { AppBar, Avatar, IconButton, Stack, Tooltip, Menu, MenuItem, Button } from "@mui/material";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

export default function HeaderBar() {
    const [ authenticated, setAuthenticated ] = useState<boolean>(false);
    const toggleAuthenticated = () => setAuthenticated(toggle => !toggle);

    const [ accountMenuAnchor, setAccountMenuAnchor ] = useState<HTMLElement | null>(null);
    const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => setAccountMenuAnchor(event.currentTarget);
    const handleCloseMenu = () => setAccountMenuAnchor(null);

    function handleLogout() {
        toggleAuthenticated();
        handleCloseMenu();
    }

    return (
        <AppBar sx={{ padding: 2, backgroundImage: appbarGradient }}>
            <Stack direction='row' spacing={2} justifyContent='space-between' alignItems='center'>
                <Link href='/'>
                    <Image src='/header-filled.svg' alt="Bulletinator Logo" width={200} height={50} />
                </Link>

                <div className="grow" />

                {
                authenticated ?
                /* Account menu */
                <>
                    <Tooltip title="Account Menu">
                        <IconButton onClick={handleOpenMenu} sx={{ p: 0}}>
                            <Avatar>
                                SH
                            </Avatar>
                        </IconButton>
                    </Tooltip>
                    <Menu
                        anchorEl={accountMenuAnchor}
                        onClose={handleCloseMenu}
                        open={accountMenuAnchor != null}
                        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                    >
                        <Link href="/account">
                            <MenuItem onClick={handleCloseMenu}>My Account</MenuItem>
                        </Link>

                        <MenuItem onClick={handleLogout}>Log Out</MenuItem>
                    </Menu>
                </>

                :
                /* Go to Login page */
                // <Link href="/login">
                    <Button onClick={toggleAuthenticated} color="inherit">Log In</Button>
                // </Link>
                }

            </Stack>
        </AppBar>
    )
}