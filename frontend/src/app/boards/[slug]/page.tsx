import BoardEditor from "@/features/boards/editor";
import HeaderBar from "@/features/layout/appbar";

export default async function BoardEditorPage({ params }: { params: Promise<{ slug: string }> }) {
    const { slug } = await params;

    return (
        <>
            <HeaderBar />
            <BoardEditor slug={slug} />
        </>
    )
}