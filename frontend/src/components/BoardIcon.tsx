/**
 * Maps a board icon string to a material icon.
 */
import SpaceDashboardIcon from '@mui/icons-material/SpaceDashboard';
import PublicIcon from '@mui/icons-material/Public';
import CreateIcon from '@mui/icons-material/Create';
import PersonIcon from '@mui/icons-material/Person';
import PeopleIcon from '@mui/icons-material/People';
import FaceIcon from '@mui/icons-material/Face';
import StarIcon from '@mui/icons-material/Star';
import HomeIcon from '@mui/icons-material/Home';
import HourglassBottomIcon from '@mui/icons-material/HourglassBottom';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import { SvgIcon, SvgIconProps } from '@mui/material';

export const boardIconTypes = ['default', 'globe', 'pencil', 'person', 'people', 'face', 'star', 'house', 'hourglass', 'money']
export type BoardIconType = 'default' | 'globe' | 'pencil' | 'person' | 'people' | 'face' | 'star' | 'house' | 'hourglass' | 'money'

export const iconMapping: Record<BoardIconType, [typeof SvgIcon, string]> = {
    default: [SpaceDashboardIcon, "Board"],
    globe: [PublicIcon, "Globe"],
    pencil: [CreateIcon, "Pencil"],
    person: [PersonIcon, "Person"],
    people: [PeopleIcon, "People"],
    face: [FaceIcon, "Face"],
    star: [StarIcon, "Star"],
    house: [HomeIcon, "House"],
    hourglass: [HourglassBottomIcon, "Hourglass"],
    money: [AttachMoneyIcon, "Money"],
}

export function BoardIcon ({ type, ...props }: { type: string } & SvgIconProps) {
    const IconElement = (Object.hasOwn(iconMapping, type) ? iconMapping[type as BoardIconType] : iconMapping.default)[0];

    return <IconElement {...props} />
}