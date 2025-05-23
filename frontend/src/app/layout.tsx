import type { Metadata } from "next";
import { AppRouterCacheProvider } from "@mui/material-nextjs/v15-appRouter";
import theme from '@/theme';
import "./globals.css";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { Roboto } from 'next/font/google';
import ContextProviders from "@/contexts";

const roboto = Roboto({
    weight: ['300', '400', '500', '700'],
    subsets: ['latin'],
    display: 'swap',
    variable: '--font-roboto',
});

export const metadata: Metadata = {
  title: "Bulletinator",
  description: "Bulletinator description",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={roboto.variable}>
      <body>
        <AppRouterCacheProvider>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <ContextProviders>
              {children}
            </ContextProviders>
          </ThemeProvider>
        </AppRouterCacheProvider>
      </body>
    </html>
  );
}
