"use client"

import { useEffect, useState } from "react"
import { Loader2, FileText, CheckCircle, Clock } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

export default function StudentResultsPage() {
    const [loading, setLoading] = useState(true)
    const [examResults, setExamResults] = useState<any[]>([])
    const [selectedResult, setSelectedResult] = useState<any>(null)

    const handleRequestReview = async (answerId: number, comment: string) => {
        try {
            await api.post(`/submissions/${answerId}/request-review`, { student_comment: comment })
            alert("Review requested submitted.")
            location.reload()
        } catch (e) {
            alert("Failed to request review")
        }
    }

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const res = await api.get("/submissions/me")
                // Group by exam
                const answers = res.data
                const groups: any = {}

                answers.forEach((ans: any) => {
                    const eId = ans.exam_id
                    if (!groups[eId]) {
                        groups[eId] = {
                            exam: ans.exam,
                            answers: [],
                            totalMarks: 0,
                            evaluatedCount: 0
                        }
                    }
                    groups[eId].answers.push(ans)
                    if (ans.evaluation) {
                        groups[eId].totalMarks += ans.evaluation.marks_awarded
                        groups[eId].evaluatedCount += 1
                    }
                })

                setExamResults(Object.values(groups))

            } catch (e) {
                console.error("Failed to load history", e)
            } finally {
                setLoading(false)
            }
        }
        fetchResults()
    }, [])

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">My Results</h1>
                <p className="text-slate-500">History of your exam submissions and grades.</p>
            </div>

            {examResults.length === 0 ? (
                <div className="text-center py-20 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                    <FileText className="w-10 h-10 text-slate-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900">No results found</h3>
                    <p className="text-slate-500 max-w-sm mx-auto mt-2">
                        You haven't taken any exams yet.
                    </p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {examResults.map((res: any, i) => (
                        <div key={i} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-lg font-bold text-slate-900">{res.exam?.title || "Unknown Exam"}</h3>
                                    <p className="text-sm text-slate-500">{new Date(res.answers[0].submitted_at).toLocaleDateString()}</p>
                                </div>
                                <div className="flex flex-col items-end">
                                    <span className="text-2xl font-bold text-slate-900">{res.totalMarks.toFixed(1)}</span>
                                    <span className="text-xs text-slate-500">Total Score</span>
                                </div>
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    {res.evaluatedCount === res.answers.length ? (
                                        <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                                            <CheckCircle className="w-3.5 h-3.5" />
                                            Graded
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-1.5 text-xs font-medium text-yellow-700 bg-yellow-50 px-2.5 py-1 rounded-full">
                                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                            Evaluating...
                                        </div>
                                    )}
                                    <span className="text-xs text-slate-400">
                                        {res.answers.length} Questions Answered
                                    </span>
                                    {res.answers.some((a: any) => a.evaluation?.review_requested) && (
                                        <div className="flex items-center gap-1.5 text-xs font-bold text-orange-600 bg-orange-50 px-2.5 py-1 rounded-full border border-orange-100 animate-pulse">
                                            <Clock className="w-3.5 h-3.5" />
                                            Review Pending
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={() => setSelectedResult(res)}
                                    className="text-sm text-indigo-600 font-medium hover:text-indigo-800"
                                >
                                    View Feedback
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Feedback Modal */}
            {selectedResult && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto flex flex-col">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
                            <div>
                                <h3 className="font-bold text-lg text-slate-900">
                                    {selectedResult.exam?.title} Details
                                </h3>
                                <p className="text-sm text-slate-500">Detailed performance review</p>
                            </div>
                            <button
                                onClick={() => setSelectedResult(null)}
                                className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-slate-500"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                            </button>
                        </div>
                        <div className="p-6 space-y-6">
                            {selectedResult.answers?.map((ans: any, idx: number) => (
                                <div key={idx} className="bg-slate-50 p-5 rounded-xl border border-slate-200">
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="flex flex-col gap-1">
                                            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                                                Question {idx + 1}
                                            </span>
                                            <p className="text-sm font-medium text-slate-900">{ans.question?.text || "Question Text Unavailable"}</p>
                                        </div>
                                        {ans.evaluation && (
                                            <span className="shrink-0 text-sm font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded">
                                                {ans.evaluation.marks_awarded} Marks
                                            </span>
                                        )}
                                    </div>

                                    <div className="mb-4 text-slate-900 bg-white p-4 rounded-lg border border-slate-200 text-sm leading-relaxed">
                                        <span className="text-xs font-semibold text-slate-400 block mb-1">YOUR ANSWER</span>
                                        {ans.answer_text || (
                                            <span className="text-slate-400 italic">Attached File: {ans.answer_file_path || "None"}</span>
                                        )}
                                    </div>

                                    {ans.evaluation ? (
                                        <div className="pl-4 border-l-2 border-emerald-500 space-y-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-4 h-4 rounded-full bg-emerald-100 flex items-center justify-center">
                                                    <CheckCircle className="w-3 h-3 text-emerald-600" />
                                                </div>
                                                <span className="text-sm font-semibold text-emerald-700">AI Feedback</span>
                                            </div>
                                            <p className="text-sm text-slate-600">
                                                {ans.evaluation.feedback}
                                            </p>

                                            {/* Teacher Comment */}
                                            {ans.evaluation.teacher_comment && (
                                                <div className="mt-3 p-3 bg-indigo-50 rounded-lg text-sm text-indigo-900 border border-indigo-100">
                                                    <span className="font-bold block text-xs uppercase tracking-wider text-indigo-500 mb-1">Teacher's Note</span>
                                                    {ans.evaluation.teacher_comment}
                                                </div>
                                            )}

                                            {/* Request Review UI */}
                                            <div className="mt-4 pt-4 border-t border-slate-100">
                                                {ans.evaluation.review_requested ? (
                                                    <div className="text-xs bg-yellow-50 text-yellow-700 px-3 py-2 rounded-lg inline-block border border-yellow-100">
                                                        <span className="font-bold">Review Pending:</span> {ans.evaluation.student_comment}
                                                    </div>
                                                ) : (
                                                    <button
                                                        onClick={() => {
                                                            const comment = prompt("Reason for review request:")
                                                            if (comment) {
                                                                handleRequestReview(ans.id, comment)
                                                            }
                                                        }}
                                                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium underline"
                                                    >
                                                        Request Manual Review
                                                    </button>
                                                )}
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
                                onClick={() => setSelectedResult(null)}
                                className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 text-slate-700"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
