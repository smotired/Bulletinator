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
        }
    },
    typography: {
        fontFamily: 'var(--font-roboto)',
    }
});

export default theme;