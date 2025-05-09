import { Stack, TextField, Button, CircularProgress, Alert } from "@mui/material"

export default function LoginFormClient() {
    return (
        <Stack spacing={2} alignItems='stretch' width='100%'>
            {/* Fields */}
            <TextField label="Email or Username" />
            <TextField label="Password" type="password" />

            {/* Login button */}

            {/* Error message */}
            <Alert severity="error">AAAH!</Alert>
        </Stack>
    )
}