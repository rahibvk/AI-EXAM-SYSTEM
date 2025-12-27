"use client"

import { useState, useEffect } from "react"
import { Loader2, AlertTriangle, CheckCircle, Search } from "lucide-react"
import api from "@/lib/api"

export default function PlagiarismPage() {
    const [courses, setCourses] = useState<any[]>([])
    const [exams, setExams] = useState<any[]>([])
    const [selectedExamId, setSelectedExamId] = useState<string>("")
    const [loading, setLoading] = useState(false)
    const [report, setReport] = useState<any[]>([])
    const [analyzed, setAnalyzed] = useState(false)

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                // Fetch logged-in teacher's courses
                // Since there isn't a dedicated "my-courses" list API that returns simple list, 
                // we'll try the generic one or use the stats one?
                // Ideally, we need a list of courses to populate the dropdown.
                // Re-using the logic from Dashboard: api.get("/users/dashboard-stats") doesn't give list.
                // Let's try fetching all courses if the user is a teacher, or implementing a specialized fetch.
                // Accessing /courses/ should generally return relevant courses.
                const coursesRes = await api.get("/courses")
                setCourses(coursesRes.data)
            } catch (e) {
                console.error("Failed to fetch courses")
            }
        }
        fetchCourses()
    }, [])

    const handleCourseChange = async (courseId: string) => {
        if (!courseId) {
            setExams([])
            return
        }
        try {
            const res = await api.get(`/exams/course/${courseId}`)
            setExams(res.data)
        } catch (e) {
            console.error(e)
        }
    }

    const runAnalysis = async () => {
        if (!selectedExamId) return
        setLoading(true)
        try {
            const res = await api.get(`/exams/${selectedExamId}/plagiarism`)
            setReport(res.data)
            setAnalyzed(true)
        } catch (e) {
            alert("Analysis failed")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Cheating Detection</h1>
                <p className="text-slate-500">Analyze subjective answers for potential plagiarism between students.</p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                    <div>
                        <label className="text-sm font-medium mb-1 block">Select Course</label>
                        <select
                            className="w-full h-10 rounded-md border border-slate-200 px-3 bg-white"
                            onChange={(e) => handleCourseChange(e.target.value)}
                        >
                            <option value="">-- Choose Course --</option>
                            {courses.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-sm font-medium mb-1 block">Select Exam</label>
                        <select
                            className="w-full h-10 rounded-md border border-slate-200 px-3 bg-white"
                            onChange={(e) => setSelectedExamId(e.target.value)}
                            disabled={!exams.length}
                        >
                            <option value="">-- Choose Exam --</option>
                            {exams.map(e => <option key={e.id} value={e.id}>{e.title}</option>)}
                        </select>
                    </div>
                </div>

                <div className="flex justify-end">
                    <button
                        onClick={runAnalysis}
                        disabled={!selectedExamId || loading}
                        className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-red-600 text-white hover:bg-red-700 h-10 px-4 transition-colors disabled:opacity-50"
                    >
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                        Run Analysis
                    </button>
                </div>
            </div>

            {analyzed && (
                <div className="space-y-4">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        Analysis Report
                        {report.length === 0 ? (
                            <span className="text-xs font-normal bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">No similarities found</span>
                        ) : (
                            <span className="text-xs font-normal bg-red-100 text-red-700 px-2 py-0.5 rounded-full">{report.length} potential flags</span>
                        )}
                    </h2>

                    {report.length > 0 ? (
                        <div className="grid gap-4">
                            {report.map((item, idx) => (
                                <div key={idx} className="bg-white p-4 rounded-lg border border-l-4 border-l-red-500 border-y-slate-200 border-r-slate-200 shadow-sm">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <h3 className="font-semibold text-slate-900">{item.student_1} <span className="text-slate-400 font-normal mx-2">vs</span> {item.student_2}</h3>
                                            <p className="text-xs text-slate-500 mt-0.5">Question: {item.question_text}</p>
                                        </div>
                                        <div className="text-right">
                                            <span className="block text-2xl font-bold text-red-600">{item.similarity_score}%</span>
                                            <span className="text-xs text-slate-500">Similarity Match</span>
                                        </div>
                                    </div>

                                    <div className="grid md:grid-cols-2 gap-4 mt-4 bg-slate-50 p-3 rounded text-sm text-slate-700">
                                        <div>
                                            <p className="text-xs font-semibold text-slate-500 mb-1">Student A Answer:</p>
                                            <p className="italic">"{item.snippet_1}"</p>
                                        </div>
                                        <div>
                                            <p className="text-xs font-semibold text-slate-500 mb-1">Student B Answer:</p>
                                            <p className="italic">"{item.snippet_2}"</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center bg-white rounded-lg border border-dashed border-slate-200">
                            <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
                            <h3 className="text-slate-900 font-medium">Clean Exam!</h3>
                            <p className="text-slate-500 text-sm">No answers exceeded the 40% similarity threshold.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
