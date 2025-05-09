/**
 * Wrapping server component for login page
 */
import { Avatar, Stack, Container, Paper, Typography } from '@mui/material';
import LockIcon from '@mui/icons-material/Lock';
import LoginFormClient from './form';

export default async function LoginForm() {
    return (
        <Container maxWidth="sm">
            <Paper sx={{ mt: 4, p: 2 }}>
                <Stack spacing={2} alignItems='center'>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <LockIcon />
                    </Avatar>
                    <Typography variant='h6' sx={{ textAlign: 'center' }}>Please log in.</Typography>

                    <LoginFormClient />
                </Stack>
            </Paper>
        </Container>
    )
}