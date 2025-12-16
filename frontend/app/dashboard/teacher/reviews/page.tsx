"use client"

import { useEffect, useState } from "react"
import api from "@/lib/api"
import { Loader2, MessageSquare, CheckCircle, Clock } from "lucide-react"

export default function TeacherReviewsPage() {
    const [loading, setLoading] = useState(true)
    const [reviews, setReviews] = useState<any[]>([])

    // Manual Grade State (Copied logic from Exam Results)
    const [selectedAnswer, setSelectedAnswer] = useState<any>(null)

    const fetchReviews = async () => {
        try {
            const res = await api.get("/submissions/pending-reviews")
            setReviews(res.data)
        } catch (error) {
            console.error("Failed to load reviews", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchReviews()
    }, [])

    const handleUpdateGrade = async (answerId: number, marks: string, comment: string) => {
        try {
            await api.post(`/submissions/${answerId}/manual-grade`, {
                marks: parseFloat(marks),
                feedback: comment
            })
            alert("Grade updated!")
            setSelectedAnswer(null) // Close modal
            fetchReviews() // Refresh list
        } catch (e) {
            alert("Error updating grade")
        }
    }

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Pending Reviews</h1>
                <p className="text-slate-500">Students have requested manual review for these answers.</p>
            </div>

            {reviews.length === 0 ? (
                <div className="bg-slate-50 border border-dashed border-slate-200 rounded-xl p-12 text-center text-slate-500">
                    <CheckCircle className="w-10 h-10 mx-auto mb-4 text-emerald-500" />
                    <h3 className="text-lg font-medium text-slate-900">All caught up!</h3>
                    <p>No pending review requests.</p>
                </div>
            ) : (
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                            <tr>
                                <th className="px-6 py-4">Student</th>
                                <th className="px-6 py-4">Exam / Question</th>
                                <th className="px-6 py-4">Student Comment</th>
                                <th className="px-6 py-4">Current Marks</th>
                                <th className="px-6 py-4 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {reviews.map((ans) => (
                                <tr key={ans.id} className="hover:bg-slate-50/50">
                                    <td className="px-6 py-4 font-medium text-slate-900">
                                        {ans.student?.full_name}
                                        <div className="text-xs text-slate-400">{ans.student?.email}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-indigo-600 mb-1">{ans.exam?.title}</div>
                                        <div className="text-xs text-slate-500 line-clamp-2 max-w-xs" title={ans.question?.text}>
                                            Q: {ans.question?.text}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="bg-orange-50 text-orange-800 p-2 rounded text-xs border border-orange-100 italic">
                                            "{ans.evaluation?.student_comment}"
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-bold">{ans.evaluation?.marks_awarded} / {ans.question?.marks}</div>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => setSelectedAnswer(ans)}
                                            className="px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700"
                                        >
                                            Review
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Review Modal */}
            {selectedAnswer && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h3 className="font-bold text-lg">Manual Grading</h3>
                            <button onClick={() => setSelectedAnswer(null)} className="text-slate-400 hover:text-slate-600">✕</button>
                        </div>
                        <div className="p-6 space-y-6">

                            {/* Question & Answer Context */}
                            <div className="space-y-4">
                                <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                                    <div className="text-xs font-bold text-slate-500 uppercase mb-1">Question</div>
                                    <p className="text-sm font-medium">{selectedAnswer.question?.text}</p>
                                    <div className="mt-2 text-xs text-slate-400">Model Answer: {selectedAnswer.question?.model_answer}</div>
                                </div>

                                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
                                    <div className="text-xs font-bold text-indigo-600 uppercase mb-1">Student Answer</div>
                                    <p className="text-sm">{selectedAnswer.answer_text}</p>
                                    {selectedAnswer.answer_file_path && (
                                        <div className="mt-2 text-xs bg-slate-100 p-1 rounded inline-block">📎 Attachment Present</div>
                                    )}
                                </div>

                                <div className="bg-red-50 p-4 rounded-lg border border-red-100">
                                    <div className="text-xs font-bold text-red-600 uppercase mb-1">Request Reason</div>
                                    <p className="text-sm italic text-red-800">"{selectedAnswer.evaluation?.student_comment}"</p>
                                </div>
                            </div>

                            {/* Grading Form */}
                            <div className="bg-slate-100 p-5 rounded-xl space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">New Marks (Max: {selectedAnswer.question?.marks})</label>
                                    <input
                                        type="number"
                                        id="new-marks"
                                        defaultValue={selectedAnswer.evaluation?.marks_awarded}
                                        className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Teacher Feedback</label>
                                    <textarea
                                        id="new-comment"
                                        className="w-full p-2 border rounded-lg h-24 focus:ring-2 focus:ring-indigo-500 outline-none"
                                        placeholder="Explain the grade change..."
                                        defaultValue={selectedAnswer.evaluation?.teacher_comment || ""}
                                    ></textarea>
                                </div>
                                <div className="flex justify-end gap-3 pt-2">
                                    <button
                                        onClick={() => setSelectedAnswer(null)}
                                        className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => {
                                            const m = (document.getElementById('new-marks') as HTMLInputElement).value
                                            const c = (document.getElementById('new-comment') as HTMLTextAreaElement).value
                                            handleUpdateGrade(selectedAnswer.id, m, c)
                                        }}
                                        className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg"
                                    >
                                        Update Grade & Resolve
                                    </button>
                                </div>
                            </div>

                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
