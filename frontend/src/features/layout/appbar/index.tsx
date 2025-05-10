/**
 * Client component for the navigation bar.
 */
"use client";

import AccountAvatar from "@/components/AccountAvatar";
import { useAuth } from "@/contexts";
import call from "@/functions";
import { logout } from "@/functions/auth";
import { appbarGradient } from "@/theme";
import { AppBar, IconButton, Stack, Tooltip, Menu, MenuItem, Button } from "@mui/material";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function HeaderBar() {
    const { authenticated, account, handleLogout } = useAuth();
    const router = useRouter();

    const [ accountMenuAnchor, setAccountMenuAnchor ] = useState<HTMLElement | null>(null);
    const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => setAccountMenuAnchor(event.currentTarget);
    const handleCloseMenu = () => setAccountMenuAnchor(null);

    function doLogout() {
        call(logout).then(() => {
            handleLogout();
            handleCloseMenu();
            router.push('/');
        });
    }

    return (
        <AppBar position="static" sx={{ padding: 2, backgroundImage: appbarGradient }}>
            <Stack direction='row' spacing={2} justifyContent='space-between' alignItems='center'>
                <Link href='/'>
                    <Image src='/header-outline.svg' alt="Bulletinator Logo" width={200} height={50} />
                </Link>

                <div className="grow" />

                {
                authenticated ?
                /* Account menu */
                <>
                    <Tooltip title="Account Menu">
                        <IconButton onClick={handleOpenMenu} sx={{ p: 0}}>
                            {/* If authenticated, account cannot be null. */}
                            <AccountAvatar account={account!} sx={{ border: '1px solid #ffffff' }} />
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

                        <MenuItem onClick={doLogout}>Log Out</MenuItem>
                    </Menu>
                </>

                :
                /* Go to Login page */
                <Link href="/login">
                    <Button color="inherit">Log In</Button>
                </Link>
                }

            </Stack>
        </AppBar>
    )
}