"use client"

import { useEffect, useState, useCallback } from "react"
import { motion } from "framer-motion"
import { Trophy, FileCheck, Clock, ArrowRight, AlertCircle, Calendar } from "lucide-react"
import api from "@/lib/api"
import Link from "next/link"

/**
 * Student Dashboard Component
 * 
 * Displays an overview of the student's progress, including:
 * - Statistical summary (Exams taken, Average Score, etc.)
 * - List of Active & Upcoming exams
 * - List of Missed exams
 * - Recent results with feedback status
 */
export default function StudentDashboard() {
    // State for dashboard statistics
    const [stats, setStats] = useState({
        examsTaken: 0,
        avgScore: 0,
        activePending: 0,
        missed: 0,
        upcoming: 0
    })
    const [recentResults, setRecentResults] = useState<any[]>([])
    const [activeExams, setActiveExams] = useState<any[]>([])
    const [missedExams, setMissedExams] = useState<any[]>([])
    const [loading, setLoading] = useState(true)

    const fetchDashboardData = useCallback(async () => {
        try {
            // Note: Maintain loading state primarily for initial fetch.
            setLoading(prev => prev && true)

            // 1. Fetch Student Submissions (Results)
            const subRes = await api.get("/submissions/me")
            const answers = subRes.data

            // Group answers by Exam ID
            const examGroups: Record<string, any> = {}
            answers.forEach((ans: any) => {
                if (!examGroups[ans.exam_id]) {
                    examGroups[ans.exam_id] = {
                        exam_id: ans.exam_id,
                        title: ans.exam?.title || "Unknown Exam",
                        total_score: 0,
                        max_marks: ans.exam?.total_marks || 0,
                        submitted_at: ans.submitted_at,
                        is_evaluated: true
                    }
                }
                const group = examGroups[ans.exam_id]
                // Update latest submission time for the exam
                if (new Date(ans.submitted_at) > new Date(group.submitted_at)) {
                    group.submitted_at = ans.submitted_at
                }

                if (ans.evaluation) {
                    group.total_score += ans.evaluation.marks_awarded
                } else {
                    group.is_evaluated = false
                }
            })

            const examResults = Object.values(examGroups).sort((a: any, b: any) =>
                new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
            )

            // Calculate Stats
            const examsTaken = examResults.length
            const evaluatedExams = examResults.filter((e: any) => e.is_evaluated)
            const totalScore = evaluatedExams.reduce((acc: number, curr: any) => acc + curr.total_score, 0)
            const avgScore = evaluatedExams.length > 0 ? Math.round(totalScore / evaluatedExams.length) : 0

            setRecentResults(examResults.slice(0, 5))

            // 2. Fetch Exams (Public Endpoint)
            const coursesRes = await api.get("/courses?limit=1000")
            const courses = coursesRes.data

            let allActive: any[] = []
            let allMissed: any[] = []
            let allUpcoming: any[] = []

            const now = new Date()

            // Get set of taken exam IDs
            const takenExamIds = new Set(examResults.map((e: any) => e.exam_id))

            // Parallel fetch for all courses
            const coursePromises = courses.map(async (course: any) => {
                try {
                    const examsRes = await api.get(`/exams/course/${course.id}`)
                    return examsRes.data
                } catch (e) {
                    console.error(`Failed to fetch exams for course ${course.id}`, e)
                    return []
                }
            })

            const coursesExamsArrays = await Promise.all(coursePromises)

            // Flatten and process
            coursesExamsArrays.flat().forEach((exam: any) => {
                if (takenExamIds.has(exam.id)) return // Skip taken

                // Ensure UTC parsing by appending Z if missing
                const getUtcDate = (dateStr: string | null) => {
                    if (!dateStr) return null
                    return new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z')
                }

                const start = getUtcDate(exam.start_time)
                const end = getUtcDate(exam.end_time)

                if (end && now > end) {
                    allMissed.push(exam)
                } else if (start && now < start) {
                    allUpcoming.push(exam)
                } else {
                    allActive.push(exam)
                }
            })

            setStats({
                examsTaken,
                avgScore,
                activePending: allActive.length + allUpcoming.length,
                missed: allMissed.length,
                upcoming: allUpcoming.length
            })

            // Combine Active and Upcoming
            const combinedActive = [...allActive, ...allUpcoming].sort((a: any, b: any) => {
                const getProps = (ex: any) => {
                    const sStr = ex.start_time || ''
                    const startRaw = sStr.endsWith('Z') ? sStr : (sStr ? sStr + 'Z' : null)
                    const sDate = startRaw ? new Date(startRaw) : new Date()

                    const eStr = ex.end_time || ''
                    const endRaw = eStr.endsWith('Z') ? eStr : (eStr ? eStr + 'Z' : null)
                    const eDate = endRaw ? new Date(endRaw) : new Date()

                    return { start: sDate, end: eDate }
                }

                const propsA = getProps(a)
                const propsB = getProps(b)

                const aIsUpcoming = propsA.start > now
                const bIsUpcoming = propsB.start > now

                if (aIsUpcoming && !bIsUpcoming) return 1
                if (!aIsUpcoming && bIsUpcoming) return -1

                if (aIsUpcoming && bIsUpcoming) {
                    return propsA.start.getTime() - propsB.start.getTime()
                }

                return propsA.end.getTime() - propsB.end.getTime()
            })

            setActiveExams(combinedActive)
            setMissedExams(allMissed)

        } catch (error) {
            console.error("Failed to fetch dashboard data", error)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchDashboardData()

        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchDashboardData, 30000)
        return () => clearInterval(interval)
    }, [fetchDashboardData])

    if (loading) return <div className="p-8 text-center">Loading dashboard...</div>

    return (
        <div className="space-y-8">
            <div>
                <div className="flex items-center gap-4">
                    <h1 className="text-3xl font-bold tracking-tight">My Learning</h1>
                    <button
                        onClick={() => fetchDashboardData()}
                        className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-all"
                        title="Refresh Dashboard"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-rotate-cw"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /></svg>
                    </button>
                </div>
                <p className="text-slate-500">Track your progress and upcoming exams.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid md:grid-cols-3 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
                >
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600">
                            <FileCheck className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Exams Taken</p>
                            <p className="text-2xl font-bold text-slate-900">{stats.examsTaken}</p>
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
                >
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-blue-50 rounded-lg text-blue-600">
                            <Clock className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Active Exams</p>
                            <p className="text-2xl font-bold text-slate-900">{stats.activePending}</p>
                        </div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
                >
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-red-50 rounded-lg text-red-600">
                            <AlertCircle className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500">Missed</p>
                            <p className="text-2xl font-bold text-slate-900">{stats.missed}</p>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Active & Missed / Recent Grid */}
            <div className="grid md:grid-cols-2 gap-8 items-start">
                {/* Left Column: Active & Missed */}
                <div className="space-y-8">
                    {/* Active Exams */}
                    <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
                        <h2 className="text-lg font-bold mb-4 sticky top-0 bg-white z-10 text-slate-800 flex items-center gap-2">
                            Active & Upcoming
                            <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{activeExams.length}</span>
                        </h2>

                        <div className="space-y-3 overflow-y-auto pr-2 custom-scrollbar max-h-[400px]">
                            {activeExams.length > 0 ? (
                                activeExams.map((exam) => (
                                    <div key={exam.id} className="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-center justify-between shrink-0 hover:border-indigo-300 transition-colors">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-semibold text-slate-900">{exam.title}</h3>
                                                {(() => {
                                                    if (!exam.start_time) return false
                                                    // Safe UTC check
                                                    const sStr = exam.start_time
                                                    const sDate = new Date(sStr.endsWith('Z') ? sStr : sStr + 'Z')
                                                    return sDate > new Date()
                                                })() && (
                                                        <span className="text-[10px] font-bold bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">UPCOMING</span>
                                                    )}
                                            </div>
                                            <p className="text-xs text-slate-500">{exam.duration_minutes} mins • {exam.total_marks} marks</p>
                                        </div>
                                        <Link
                                            href={`/dashboard/student/exams/${exam.id}`}
                                            className="p-2 bg-white text-indigo-600 rounded-lg border border-slate-200 hover:bg-indigo-50 hover:border-indigo-200 transition-all shadow-sm"
                                        >
                                            <ArrowRight className="w-4 h-4" />
                                        </Link>
                                    </div>
                                ))
                            ) : (
                                <div className="p-8 text-center border border-dashed border-slate-200 rounded-lg">
                                    <p className="text-slate-500 text-sm">No active exams right now.</p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Missed Exams */}
                    {missedExams.length > 0 && (
                        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
                            <h2 className="text-lg font-bold mb-4 text-slate-800 flex items-center gap-2">
                                Missed Exams
                                <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{missedExams.length}</span>
                            </h2>
                            <div className="space-y-3 overflow-y-auto pr-2 custom-scrollbar max-h-[300px]">
                                {missedExams.map((exam) => (
                                    <div key={exam.id} className="bg-red-50/50 p-4 rounded-lg border border-red-100 flex items-center justify-between opacity-75 hover:opacity-100 transition-opacity shrink-0">
                                        <div>
                                            <h3 className="font-medium text-slate-700">{exam.title}</h3>
                                            <p className="text-xs text-red-500 mt-1">Ended {new Date(exam.end_time).toLocaleDateString()}</p>
                                        </div>
                                        <div className="text-[10px] font-bold text-red-500 bg-red-100 px-2 py-1 rounded">
                                            EXPIRED
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>

                {/* Right Column: Recent Activity */}
                <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-full max-h-[800px] flex flex-col">
                    <h2 className="text-lg font-bold mb-4 text-slate-800 flex items-center gap-2">
                        Recent Results
                        <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{recentResults.length}</span>
                    </h2>
                    <div className="space-y-3 overflow-y-auto pr-2 flex-1 custom-scrollbar min-h-[300px]">
                        {recentResults.length > 0 ? (
                            recentResults.map((result) => (
                                <div key={result.exam_id} className="bg-slate-50 p-4 rounded-lg border border-slate-200 flex items-center justify-between shrink-0">
                                    <div>
                                        <h3 className="font-semibold text-slate-900">{result.title}</h3>
                                        <div className="flex items-center gap-2 mt-1">
                                            {result.is_evaluated ? (
                                                <span className="text-sm font-bold text-slate-700">{result.total_score} <span className="text-slate-400 text-xs font-normal">/ {result.max_marks}</span></span>
                                            ) : (
                                                <span className="text-xs text-yellow-600 font-medium">Evaluating...</span>
                                            )}
                                        </div>
                                        <p className="text-[10px] text-slate-400 mt-1">{new Date(result.submitted_at).toLocaleDateString()}</p>
                                    </div>
                                    {result.is_evaluated ? (
                                        <div className="p-2 bg-emerald-100 text-emerald-700 rounded-lg">
                                            <Trophy className="w-4 h-4" />
                                        </div>
                                    ) : (
                                        <div className="p-2 bg-yellow-100 text-yellow-700 rounded-lg">
                                            <Clock className="w-4 h-4" />
                                        </div>
                                    )}
                                </div>
                            ))
                        ) : (
                            <div className="p-8 text-center border border-dashed border-slate-200 rounded-lg mt-10">
                                <p className="text-slate-500 text-sm">No completed exams yet.</p>
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </div>
    )
}
