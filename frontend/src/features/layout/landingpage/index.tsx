import { Container, Typography } from "@mui/material";
import Image from "next/image";

export default async function LandingPageContent() {
    return (
        <Container sx={{ pt: 4 }}>
            <Image src='/header-text.png' alt="Bulletinator" width={512} height={64} className="mx-auto"/>
            <Typography sx={{ textAlign: 'center' }}>Coming soon!</Typography>
        </Container>
    )
}