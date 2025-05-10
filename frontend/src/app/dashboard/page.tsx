/**
 * Dashboard page contains 
 */

import Dashboard from "@/features/boards/dashboard";
import HeaderBar from "@/features/layout/appbar";

export default async function DashboardPage() {
    return (
        <>
            <HeaderBar />
            <Dashboard />
        </>
    )
}