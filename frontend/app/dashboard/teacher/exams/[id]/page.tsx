"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, ArrowLeft, User, Award, FileText } from "lucide-react"
import api from "@/lib/api"

export default function ExamResultsPage() {
    const params = useParams()
    const router = useRouter()
    const examId = params.id

    const [loading, setLoading] = useState(true)
    const [submissions, setSubmissions] = useState<any[]>([])
    const [exam, setExam] = useState<any>(null)
    const [reEvaluating, setReEvaluating] = useState(false)
    const [selectedStudent, setSelectedStudent] = useState<any>(null)

    const handleReEvaluate = async () => {
        if (!confirm("This will trigger AI evaluation for any ungraded answers. Continue?")) return
        setReEvaluating(true)
        try {
            await api.post(`/submissions/${examId}/evaluate`)
            alert("Evaluation Access Triggered. Please refresh in a few moments.")
            location.reload()
        } catch (err: any) {
            alert("Failed to start evaluation: " + (err.response?.data?.detail || err.message))
        } finally {
            setReEvaluating(false)
        }
    }

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Exam Details
                const examRes = await api.get(`/exams/${examId}`)
                setExam(examRes.data)

                // Fetch Submissions
                const subRes = await api.get(`/submissions/${examId}/all`)
                setSubmissions(subRes.data)
            } catch (err) {
                console.error("Failed to load results")
            } finally {
                setLoading(false)
            }
        }
        if (examId) fetchData()
    }, [examId])

    // Group answers by student (since 1 exam has many questions, backend returns list of ALL answers)
    // We need to aggregate them per student.
    const studentResults = submissions.reduce((acc: any, sub: any) => {
        const sId = sub.student_id
        if (!acc[sId]) {
            acc[sId] = {
                student: sub.student,
                answers: [], // Start empty array to collect answers
                totalMarks: 0,
                maxMarks: 0,
                answersCount: 0,
                evaluatedCount: 0
            }
        }

        acc[sId].answers.push(sub) // Collect answers

        if (sub.evaluation) {
            acc[sId].totalMarks += sub.evaluation.marks_awarded
            acc[sId].evaluatedCount += 1
        }
        acc[sId].answersCount += 1
        return acc
    }, {})

    const students = Object.values(studentResults)

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex items-center gap-4">
                <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-slate-500" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">{exam?.title || "Exam"} Results</h1>
                    <p className="text-slate-500">View student performance and AI evaluations.</p>
                </div>
                <div className="ml-auto">
                    <button
                        onClick={() => handleReEvaluate()}
                        disabled={reEvaluating}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                    >
                        {reEvaluating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Award className="w-4 h-4" />}
                        Re-run AI Grading
                    </button>
                </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <table className="w-full text-sm text-left">
                    <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
                        <tr>
                            <th className="px-6 py-4">Student</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Questions Answered</th>
                            <th className="px-6 py-4">Total Score</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr >
                    </thead >
                    <tbody className="divide-y divide-slate-100">
                        {students.length === 0 ? (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                                    No submissions yet.
                                </td>
                            </tr>
                        ) : (
                            students.map((res: any, i) => (
                                <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 py-4 font-medium text-slate-900 flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center">
                                            <User className="w-4 h-4" />
                                        </div>
                                        <div>
                                            <div>{res.student?.full_name || "Unknown Student"}</div>
                                            {/* Check for review requests in answers */}
                                            {res.answers.some((a: any) => a.evaluation?.review_requested) && (
                                                <span className="text-[10px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded ml-2 font-bold">REVIEW REQUESTED</span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        {res.evaluatedCount === res.answersCount ? (
                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">
                                                Graded
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-50 text-yellow-700">
                                                In Progress
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">
                                        {res.answersCount} Questions
                                    </td>
                                    <td className="px-6 py-4 font-bold text-slate-900">
                                        {res.totalMarks.toFixed(1)}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedStudent(res)}
                                            className="text-indigo-600 hover:text-indigo-800 font-medium text-xs"
                                        >
                                            View Details
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table >
            </div >

            {/* Detail Modal */}
            {
                selectedStudent && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
                        <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto flex flex-col">
                            <div className="p-6 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
                                <div>
                                    <h3 className="font-bold text-lg text-slate-900">
                                        Submission Details
                                    </h3>
                                    <p className="text-sm text-slate-500">{selectedStudent.student?.full_name}</p>
                                </div>
                                <button
                                    onClick={() => setSelectedStudent(null)}
                                    className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-slate-500"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                                </button>
                            </div>
                            <div className="p-6 space-y-6">
                                {selectedStudent.answers?.map((ans: any, idx: number) => (
                                    <div key={idx} className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                                        <div className="flex justify-between items-start mb-3">
                                            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                                Question {idx + 1}
                                            </span>
                                            {ans.evaluation && (
                                                <span className="text-sm font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                                                    {ans.evaluation.marks_awarded} Marks
                                                </span>
                                            )}
                                        </div>

                                        <div className="mb-4 text-slate-900 bg-white p-4 rounded-lg border border-slate-200 text-sm leading-relaxed">
                                            {ans.answer_text || (
                                                <span className="text-slate-400 italic">Attached File: {ans.answer_file_path || "None"}</span>
                                            )}
                                        </div>

                                        {ans.evaluation ? (
                                            <div className="pl-4 border-l-2 border-emerald-500 space-y-4">
                                                <div className="flex items-center gap-2">
                                                    <Award className="w-4 h-4 text-emerald-600" />
                                                    <span className="text-sm font-semibold text-emerald-700">AI Feedback</span>
                                                </div>
                                                <p className="text-sm text-slate-600">
                                                    {ans.evaluation.feedback}
                                                </p>

                                                {/* Review Request Block */}
                                                {ans.evaluation.review_requested && (
                                                    <div className="bg-red-50 p-3 rounded-lg border border-red-100">
                                                        <h4 className="text-xs font-bold text-red-600 uppercase mb-1">Student Review Request</h4>
                                                        <p className="text-sm text-red-800 italic">"{ans.evaluation.student_comment}"</p>
                                                    </div>
                                                )}

                                                {/* Manual Grading Controls (Always visible to allow overrides) */}
                                                <div className="pt-2">
                                                    <details className="text-xs">
                                                        <summary className="cursor-pointer text-indigo-600 font-medium mb-2">Edit Grade / Manual Review</summary>
                                                        <div className="mt-2 space-y-3 bg-slate-100 p-3 rounded-lg">
                                                            <div>
                                                                <label className="block text-slate-500 mb-1">New Marks</label>
                                                                <input
                                                                    type="number"
                                                                    defaultValue={ans.evaluation.marks_awarded}
                                                                    id={`marks-${ans.id}`}
                                                                    className="w-20 p-1 border rounded text-sm"
                                                                />
                                                            </div>
                                                            <div>
                                                                <label className="block text-slate-500 mb-1">Teacher Comment</label>
                                                                <textarea
                                                                    id={`comment-${ans.id}`}
                                                                    defaultValue={ans.evaluation.teacher_comment || ""}
                                                                    className="w-full p-2 border rounded text-sm"
                                                                    placeholder="Reason for changing grade..."
                                                                />
                                                            </div>
                                                            <button
                                                                onClick={async () => {
                                                                    const m = (document.getElementById(`marks-${ans.id}`) as HTMLInputElement).value
                                                                    const c = (document.getElementById(`comment-${ans.id}`) as HTMLTextAreaElement).value
                                                                    try {
                                                                        await api.post(`/submissions/${ans.id}/manual-grade`, {
                                                                            marks: parseFloat(m),
                                                                            feedback: c
                                                                        })
                                                                        alert("Grade updated!")
                                                                        location.reload()
                                                                    } catch (e) { alert("Error updating grade") }
                                                                }}
                                                                className="px-3 py-1 bg-indigo-600 text-white rounded text-xs"
                                                            >
                                                                Update Grade
                                                            </button>
                                                        </div>
                                                    </details>
                                                </div>

                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2 text-yellow-600 text-sm bg-yellow-50 p-3 rounded-lg border border-yellow-100">
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Analysis in progress...
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            <div className="p-4 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end">
                                <button
                                    onClick={() => setSelectedStudent(null)}
                                    className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 text-slate-700"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    )
}
