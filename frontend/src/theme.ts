"use client";
import { createTheme } from "@mui/material/styles";

const theme = createTheme({
    palette: {
        primary: {
            light: '#3730a3',
            main: '#312e81',
            dark: '#1e1b4b',
        },
        secondary: {
            light: '#10b981',
            main: '#059669',
            dark: '#047857',
        },
    },
    typography: {
        fontFamily: 'var(--font-roboto)',
    }
});

export default theme;

// Gradient for the app bar
export const appbarGradient = `
    radial-gradient(circle at 130% -40%, var(--color-emerald-600) 10%, transparent 80%),
    radial-gradient(circle at 80% 180%, var(--color-indigo-800) 20%, transparent 60%),
    radial-gradient(circle at 0% 100%, var(--color-indigo-950) 24%, transparent 80%);
`;