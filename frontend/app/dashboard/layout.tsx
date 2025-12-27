"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
    LayoutDashboard,
    BookOpen,
    FileText,
    MessageSquare,
    Settings,
    LogOut,
    Menu,
    X,
    AlertTriangle
} from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const [isSidebarOpen, setSidebarOpen] = useState(true)
    const [role, setRole] = useState<string | null>(null)
    const pathname = usePathname()
    const router = useRouter()

    useEffect(() => {
        // Check auth
        const checkAuth = async () => {
            try {
                const res = await api.get("/me")
                setRole(res.data.role)
            } catch (e) {
                router.push("/login")
            }
        }
        checkAuth()
    }, [])

    const navItems = role === 'teacher' ? [
        { href: "/dashboard/teacher", label: "Overview", icon: LayoutDashboard },
        { href: "/dashboard/teacher/courses", label: "My Courses", icon: BookOpen },
        { href: "/dashboard/teacher/exams", label: "Exams", icon: FileText },
        { href: "/dashboard/teacher/reviews", label: "Pending Reviews", icon: MessageSquare },
        { href: "/dashboard/teacher/bulk-upload", label: "Bulk Upload", icon: FileText },
        { href: "/dashboard/teacher/plagiarism", label: "Cheating Detection", icon: AlertTriangle },
    ] : [
        { href: "/dashboard/student", label: "My Learning", icon: LayoutDashboard },
        { href: "/dashboard/student/courses", label: "Browse Courses", icon: BookOpen },
        { href: "/dashboard/student/results", label: "My Results", icon: FileText },
    ]

    return (
        <div className="min-h-screen bg-slate-50 flex">
            {/* Sidebar */}
            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-white transition-transform duration-300 lg:translate-x-0 lg:static lg:block",
                    isSidebarOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="h-16 flex items-center px-6 font-bold text-xl tracking-tight border-b border-slate-800">
                    AI Exam System
                </div>

                <nav className="p-4 space-y-2">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-slate-400 hover:text-white hover:bg-slate-800",
                                pathname === item.href && "text-white bg-slate-800"
                            )}
                        >
                            <item.icon className="w-5 h-5" />
                            {item.label}
                        </Link>
                    ))}
                </nav>

                <div className="absolute bottom-4 left-4 right-4">
                    <button
                        onClick={() => {
                            localStorage.removeItem("token")
                            router.push("/login")
                        }}
                        className="flex items-center gap-3 px-3 py-2 w-full rounded-md text-red-400 hover:bg-slate-800 transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 text-slate-900">
                <header className="h-16 bg-white border-b border-slate-100 flex items-center px-4 lg:hidden">
                    <button onClick={() => setSidebarOpen(!isSidebarOpen)}>
                        {isSidebarOpen ? <X /> : <Menu />}
                    </button>
                </header>

                <main className="flex-1 p-6 overflow-auto">
                    {children}
                </main>
            </div>
        </div>
    )
}
