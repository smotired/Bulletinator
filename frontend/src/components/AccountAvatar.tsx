import { colorFromString } from "@/app/utils/color";
import { Account } from "@/types";
import { Avatar, AvatarProps } from "@mui/material";

export default function AccountAvatar({ account, ...avatarProps }: AvatarProps & { account: Account }) {
    // Convert account name to capitalized initials
    const name = account.display_name || account.username;
    const contents = (name.includes(' ') ? `${name.split(' ')[0][0]}${name.split(' ')[1][0]}` : name[0]).toUpperCase();
    
    // Also come up with a color
    const color = colorFromString(name);

    return (
        <Avatar {...avatarProps} src={account.profile_image || ''} sx={{ ...avatarProps.sx, bgcolor: color }}>
            { account.profile_image ? avatarProps.children : contents }
        </Avatar>
    )
}