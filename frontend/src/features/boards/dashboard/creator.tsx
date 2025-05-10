/**
 * Addition button and modal for adding a board
 */
"use client";
import { Alert, Box, Button, Dialog, Divider, FormControlLabel, Grid, IconButton, MenuItem, Stack, Switch, TextField, Tooltip, Typography } from "@mui/material";
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { convertToIdentifier } from "@/app/utils/board";
import { useAuth } from "@/contexts";
import { BoardIconType, boardIconTypes, iconMapping } from "@/components/BoardIcon";
import call from "@/functions";
import { createBoard } from "@/functions/boards";
import { useRouter } from "next/navigation";

type BoardConfig = { name: string, identifier: string, icon: string, public: boolean };

export default function BoardCreator() {
    const { account } = useAuth();
    const router = useRouter();

    const [ submitDisabled, setSubmitDisabled ] = useState<boolean>(true);
    const [ config, setConfig ] = useState<BoardConfig | null>(null);
    const [ error, setError ] = useState<string | null>(null);


    const [ name, setName ] = useState<string>('');
    const handleNameChange = (event: ChangeEvent<HTMLInputElement>) => setName(event.target.value);

    const [ icon, setIcon ] = useState<BoardIconType>('default');
    const handleIconChange = (event: ChangeEvent<HTMLInputElement>) => setIcon(event.target.value as BoardIconType);

    const [ identifier, setIdentifier ] = useState<string>('');
    const handleIdentifierChange = (event: ChangeEvent<HTMLInputElement>) => setIdentifier(event.target.value);

    const [ isPublic, setIsPublic ] = useState<boolean>(false);
    const handlePublicChange = (event: ChangeEvent<HTMLInputElement>) => setIsPublic(event.target.checked);

    const trueIdentifier = identifier ? convertToIdentifier(identifier) : convertToIdentifier(name);

    const [ dialogOpen, setDialogOpen ] = useState<boolean>(false);
    const toggleDialog = () => setDialogOpen(toggle => !toggle);

    const [ showToast, setShowToast ] = useState<boolean>(false);
    const toggleToast = () => setShowToast(toggle => !toggle);

    // On name change, set disabled if necessary.
    useEffect(() => setSubmitDisabled(convertToIdentifier(name).length == 0 || trueIdentifier.length == 0), [name]);

    function handleSubmit(event: FormEvent) {
        event.preventDefault();
        setConfig({ name, identifier, icon, public: isPublic });
        setError(null);
    }
    useEffect(() => {
        if (config == null) return;

        call(createBoard, config)
            .then((board) => {
                router.refresh(); // fetch new board
                setConfig(null);
                setShowToast(true); // Show the toast
                setDialogOpen(false); // Close the dialog
                // Reset form state
                setName('');
                setIcon('default');
                setIdentifier('');
                setIsPublic(false);
            })
            .catch((error: Error) => {
                setConfig(null);
                setError(error.message);
            })
    }, [config]);

    return (
        <>
            <Tooltip title="Create Board">
                <IconButton onClick={toggleDialog} color="primary">
                    <AddIcon />
                </IconButton>
            </Tooltip>

            <Dialog open={dialogOpen} onClose={toggleDialog} fullWidth maxWidth='sm'>
                <Stack direction='row' sx={{ p: 1, pl: 2 }} alignItems='center'>
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>Create Board</Typography>
                    <Tooltip title="Close Dialog">
                        <IconButton onClick={toggleDialog}>
                            <CloseIcon />
                        </IconButton>
                    </Tooltip>
                </Stack>
                <Divider />

                <form onSubmit={handleSubmit}>
                    <Grid container spacing={2} sx={{ p: 2, width: '100%' }}>

                        <Grid size={{ xs: 12, sm: 8 }}>
                            <TextField value={name} required onChange={handleNameChange} variant="outlined" label="Board Name" fullWidth />
                        </Grid>
                            
                        <Grid size={{ xs: 12, sm: 4 }}>
                            <TextField value={icon} required select onChange={handleIconChange} variant="outlined" label="Icon" fullWidth>
                                {
                                    boardIconTypes.toSorted().map((type: string) => {
                                        const [ IconElement, label ] = iconMapping[type as BoardIconType];
                                        return (
                                            <MenuItem value={type}>
                                                <Box sx={{ display: 'flex', gap: '0.5rem', flexDirection: 'row', alignItems: 'center' }}>
                                                    <IconElement color='disabled' />
                                                    {label}
                                                </Box>
                                            </MenuItem>
                                        )
                                    })
                                }
                            </TextField>
                        </Grid>

                        <Grid size={8}>
                            <TextField value={identifier} onChange={handleIdentifierChange} variant="outlined" label="Identifier" fullWidth />
                        </Grid>
                            
                        <Grid size={4} sx={{ display: 'flex', direction: 'flex-row', gap: '0.5rem', alignItems: 'center' }}>
                            <FormControlLabel checked={isPublic} control={<Switch onChange={handlePublicChange} />} label="Public" />
                        </Grid>

                        <Grid size={12}>
                            <Button loading={config != null} disabled={submitDisabled} type="submit" variant="contained" fullWidth>Create Board</Button>
                        </Grid>

                        { error && <Grid size={12}> <Alert severity="error">{error}</Alert> </Grid> }

                        { (name || identifier) && <Grid size={12}> <Typography noWrap variant="caption" sx={{ display: 'block' }}>Will be saved under /boards/{account!.username}-{trueIdentifier}</Typography> </Grid> }
                    </Grid>
                </form>
            </Dialog>
        </>
    )
}
