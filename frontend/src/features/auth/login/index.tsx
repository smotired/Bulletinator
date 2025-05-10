/**
 * Wrapping server component for login page
 */
import { Stack, Container, Paper, Typography } from '@mui/material';
import Image from 'next/image';
import LoginFormClient from './form';

export default async function LoginForm() {
    return (
        <Container maxWidth="sm">
            <Paper sx={{ mt: 4, p: 2 }}>
                <Stack spacing={2} alignItems='center'>
                    <Image src='/header-text.png' alt="Bulletinator" width={512} height={64} className="mx-auto"/>
                    <Typography variant='h6' sx={{ textAlign: 'center' }}>Please log in.</Typography>

                    <LoginFormClient />
                </Stack>
            </Paper>
        </Container>
    )
}