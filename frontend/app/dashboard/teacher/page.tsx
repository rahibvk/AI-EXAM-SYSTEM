"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Users, BookOpen, FileCheck } from "lucide-react"
import api from "@/lib/api"

export default function TeacherDashboard() {
    const [stats, setStats] = useState({ courses: 0, exams: 0, students: 0, pendingReviews: 0 })

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Stats
                const statsRes = await api.get("/users/dashboard-stats")
                setStats({
                    courses: statsRes.data.courses,
                    students: statsRes.data.students,
                    pendingReviews: statsRes.data.pending_reviews,
                    exams: 0 // Not returned yet, but we can ignore or add later
                })
            } catch (e) {
                console.error("Failed to load dashboard stats", e)
            }
        }
        fetchData()
    }, [])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Dashboard Overview</h1>
                <p className="text-slate-500">Welcome back, Professor.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                {[
                    { label: "Active Courses", value: stats.courses, icon: BookOpen, color: "bg-blue-500" },
                    { label: "Pending Reviews", value: stats.pendingReviews, icon: FileCheck, color: "bg-orange-500" },
                    { label: "Total Students", value: stats.students, icon: Users, color: "bg-emerald-500" }
                ].map((stat, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="p-6 bg-white rounded-xl shadow-sm border border-slate-100 flex items-center gap-4 text-slate-900"
                    >
                        <div className={`${stat.color} p-3 rounded-lg text-white`}>
                            <stat.icon className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                            <h3 className="text-2xl font-bold">{stat.value}</h3>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Recent Activity Section could go here */}
        </div>
    )
}
