"use client"

import { motion } from "framer-motion"

export default function StudentDashboard() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">My Learning</h1>
                <p className="text-slate-500">Track your progress and upcoming exams.</p>
            </div>

            <div className="p-8 text-center bg-white rounded-xl border border-slate-100 shadow-sm">
                <p className="text-slate-500">You are enrolled in the AI System Demo Course.</p>
            </div>
        </div>
    )
}
