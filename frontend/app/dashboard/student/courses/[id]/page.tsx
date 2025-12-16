"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { ArrowLeft, FileText, PlayCircle, Loader2, Clock } from "lucide-react"
import api from "@/lib/api"

interface Exam {
    id: number
    title: string
    description: string
    duration_minutes: number
    total_marks: number
    questions: any[]
}

export default function StudentCourseDetailPage() {
    const params = useParams()
    const router = useRouter()
    const id = params.id

    const [exams, setExams] = useState<Exam[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchExams = async () => {
            try {
                const res = await api.get(`/exams/course/${id}`)
                setExams(res.data)
            } catch (error) {
                console.error("Failed to fetch exams")
            } finally {
                setLoading(false)
            }
        }
        if (id) fetchExams()
    }, [id])

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>

    return (
        <div className="space-y-8">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/student/courses" className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-slate-500" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Course Exams</h1>
                    <p className="text-slate-500">Select an exam to start assessment.</p>
                </div>
            </div>

            <div className="space-y-4">
                {exams.length === 0 ? (
                    <div className="p-8 text-center bg-slate-50 rounded-lg">
                        <p className="text-slate-500">No exams available for this course yet.</p>
                    </div>
                ) : (
                    exams.map((exam) => (
                        <div key={exam.id} className="bg-white border border-slate-200 rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-indigo-300 transition-colors">
                            <div>
                                <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-semibold text-lg">{exam.title}</h3>
                                    <span className="bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full font-medium">
                                        {exam.total_marks} Marks
                                    </span>
                                </div>
                                <p className="text-slate-500 text-sm mb-2">{exam.description}</p>
                                <div className="flex items-center gap-4 text-xs text-slate-400">
                                    <div className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {exam.duration_minutes} Mins
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <FileText className="w-3 h-3" />
                                        {exam.questions?.length || 0} Questions
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => router.push(`/dashboard/student/exams/${exam.id}`)}
                                className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 h-10 px-6 py-2 min-w-[120px]"
                            >
                                <PlayCircle className="mr-2 h-4 w-4" />
                                Start
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}
