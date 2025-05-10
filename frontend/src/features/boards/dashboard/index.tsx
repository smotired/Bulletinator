import CookieSetter from "@/components/CookieSetter";
import { getEditableBoards } from "@/functions/boards";
import BoardList from "./list";

export default async function Dashboard() {
    const [ boards, cookies ] = await getEditableBoards();

    return (
        <>
            <CookieSetter settings={cookies} />
            <BoardList boards={boards} />
        </>
    )
}