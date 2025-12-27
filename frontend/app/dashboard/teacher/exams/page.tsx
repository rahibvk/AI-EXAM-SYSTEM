"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2, FileText, Calendar, Clock, ArrowRight, Search } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

interface Exam {
    id: number
    title: string
    course_id: number
    start_time: string | null
    end_time: string | null
    duration_minutes: number
    mode: string
    total_marks: number
}

interface Course {
    id: number
    title: string
    code: string
}

export default function TeacherExamsPage() {
    const router = useRouter()
    const [loading, setLoading] = useState(true)
    const [exams, setExams] = useState<(Exam & { courseTitle: string })[]>([])
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all") // all, online, offline

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Get Courses
                const coursesRes = await api.get("/courses/my-courses")
                const courses: Course[] = coursesRes.data

                // 2. Get Exams for each course
                let allExams: (Exam & { courseTitle: string })[] = []

                // Fetch in parallel
                await Promise.all(courses.map(async (course) => {
                    try {
                        const examsRes = await api.get(`/exams/course/${course.id}`)
                        const courseExams = examsRes.data.map((e: Exam) => ({ ...e, courseTitle: course.title }))
                        allExams = [...allExams, ...courseExams]
                    } catch (e) {
                        console.error(`Failed to fetch exams for course ${course.id}`, e)
                    }
                }))

                // Sort by ID desc (newest first)
                allExams.sort((a, b) => b.id - a.id)
                setExams(allExams)

            } catch (error) {
                console.error("Failed to load data", error)
            } finally {
                setLoading(false)
            }
        }
        fetchData()
    }, [])

    const filteredExams = exams.filter(exam => {
        const matchesSearch = exam.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            exam.courseTitle.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === "all" || exam.mode === statusFilter
        return matchesSearch && matchesStatus
    })

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">My Exams</h1>
                    <p className="text-slate-500">Manage exams across all your courses.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            placeholder="Search exams..."
                            className="pl-9 pr-4 h-10 rounded-md border border-slate-200 text-sm focus:ring-2 focus:ring-slate-900 w-full md:w-64"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <select
                        className="h-10 rounded-md border border-slate-200 px-3 text-sm bg-white"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="all">All Modes</option>
                        <option value="online">Online</option>
                        <option value="offline">Offline</option>
                    </select>
                </div>
            </div>

            {filteredExams.length === 0 ? (
                <div className="text-center py-20 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                    <FileText className="w-10 h-10 text-slate-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900">No exams found</h3>
                    <p className="text-slate-500 max-w-sm mx-auto mt-2">
                        Go to a course to generate or create a new exam.
                    </p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {filteredExams.map((exam) => (
                        <div key={exam.id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow flex items-center justify-between group">
                            <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                                        {exam.courseTitle}
                                    </span>
                                    <span className={cn("text-xs font-medium px-2 py-1 rounded border",
                                        exam.mode === 'online' ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-orange-50 text-orange-700 border-orange-100"
                                    )}>
                                        {exam.mode.toUpperCase()}
                                    </span>
                                </div>
                                <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                                    {exam.title}
                                </h3>
                                <div className="flex items-center gap-4 text-sm text-slate-500">
                                    <div className="flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        <span>{exam.duration_minutes} mins</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Calendar className="w-4 h-4" />
                                        <span>{exam.start_time ? new Date(exam.start_time).toLocaleDateString() : "No Date"}</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => router.push(`/dashboard/teacher/exams/${exam.id}`)}
                                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors"
                            >
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
