import { AuthenticatedAccount } from "@/types";
import { Avatar, AvatarProps } from "@mui/material";

export default function AccountAvatar({ account, ...avatarProps }: AvatarProps & { account: AuthenticatedAccount }) {
    // Convert account name to capitalized initials
    const name = account.display_name || account.username;
    const contents = (name.includes(' ') ? `${name.split(' ')[0][0]}${name.split(' ')[1][0]}` : name[0]).toUpperCase();
    
    // Also come up with a color
    /* eslint-disable no-bitwise */
    let hash = 0, i = 0;
    for (i = 0; i < name.length; i++)
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    let color = '#';
    for (i = 0; i < 3; i += 1) {
        const value = (hash >> (i * 8)) & 0xff;
        color += `00${value.toString(16)}`.slice(-2);
    }
    /* eslint-enable no-bitwise */

    return (
        <Avatar {...avatarProps} src={account.profile_image} sx={{ ...avatarProps.sx, bgcolor: color }}>
            { account.profile_image ? avatarProps.children : contents }
        </Avatar>
    )
}