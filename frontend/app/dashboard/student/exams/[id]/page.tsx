"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, ArrowRight, ArrowLeft, Upload, CheckCircle, Clock } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"
import { parseQuestionText } from "@/lib/examUtils"

interface Question {
    id: number
    text: string
    marks: number
    question_type: string
}

interface Exam {
    id: number
    title: string
    duration_minutes: number
    questions: Question[]
    mode?: "online" | "offline"
}

export default function TakeExamPage() {
    const params = useParams()
    const router = useRouter()
    const examId = params.id

    const [exam, setExam] = useState<Exam | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)
    const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0)

    // Timer State
    const [timeLeft, setTimeLeft] = useState<number | null>(null) // in seconds

    // Store answers: { questionId: { text: string, file: File | null } }
    const [answers, setAnswers] = useState<Record<number, { text: string, file: File | null }>>({})

    // Bulk Upload State (Moved up to fix Hooks Rule)
    const [bulkFiles, setBulkFiles] = useState<File[]>([])

    useEffect(() => {
        const fetchExam = async () => {
            try {
                const res = await api.get(`/exams/${examId}`)
                const examData = res.data
                setExam(examData)
                setTimeLeft(examData.duration_minutes * 60)
            } catch (error: any) {
                console.error("Failed to load exam")
                if (error.response?.status === 403) {
                    setError(error.response.data.detail || "Access Denied")
                } else {
                    setError("Failed to load exam.")
                }
            } finally {
                setLoading(false)
            }
        }
        if (examId) fetchExam()
    }, [examId])

    // Timer Tick
    useEffect(() => {
        if (timeLeft === null || timeLeft <= 0) return

        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev === null) return null
                if (prev <= 1) {
                    clearInterval(timer)
                    handleAutoSubmit()
                    return 0
                }
                return prev - 1
            })
        }, 1000)

        return () => clearInterval(timer)
    }, [timeLeft])

    const handleAutoSubmit = () => {
        if (submitting) return;
        alert("Time is up! Your exam is being submitted automatically.")
        handleSubmit(true)
    }

    const handleTextChange = (text: string) => {
        if (!exam) return
        const qId = exam.questions[currentQuestionIdx].id
        setAnswers(prev => ({
            ...prev,
            [qId]: { ...prev[qId], text }
        }))
    }

    const formatTime = (seconds: number) => {
        const m = Math.floor(seconds / 60)
        const s = seconds % 60
        return `${m}:${s.toString().padStart(2, '0')}`
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!exam || !e.target.files?.length) return
        const file = e.target.files[0]
        const qId = exam.questions[currentQuestionIdx].id
        setAnswers(prev => ({
            ...prev,
            [qId]: { ...prev[qId], file }
        }))
    }

    const handleSubmit = async (auto = false) => {
        if (!exam) return
        if (!auto && !confirm("Are you sure you want to submit your exam?")) return

        setSubmitting(true)
        try {
            const payload = {
                exam_id: exam.id,
                answers: exam.questions.map(q => ({
                    question_id: q.id,
                    answer_text: answers[q.id]?.text || "",
                    answer_file_path: null // In future need real upload handling via FormData but backend needs update for that. For now text.
                }))
            }
            await api.post("/submissions/submit", payload)
            router.push("/dashboard/student/results")
        } catch (err: any) {
            alert("Submission failed: " + (err.response?.data?.detail || err.message))
            setSubmitting(false)
        }
    }

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>

    if (error) return (
        <div className="flex h-[50vh] flex-col items-center justify-center space-y-4">
            <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-100 max-w-md text-center shadow-sm">
                <h3 className="font-bold text-lg mb-2">Access Denied</h3>
                <p>{error}</p>
                <button onClick={() => router.back()} className="mt-4 px-4 py-2 bg-white border border-red-200 rounded-lg text-sm font-medium hover:bg-red-50">
                    Go Back
                </button>
            </div>
        </div>
    )

    if (!exam) return null;

    // Helper to check mode
    const isOffline = exam.mode === "offline"

    const handleBulkFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setBulkFiles(Array.from(e.target.files))
        }
    }

    const handleBulkSubmit = async () => {
        if (bulkFiles.length === 0) {
            alert("Please upload at least one answer sheet.")
            return
        }
        if (!confirm("Confirm submission of " + bulkFiles.length + " pages?")) return

        setSubmitting(true)
        try {
            const formData = new FormData()
            bulkFiles.forEach((file) => {
                formData.append("files", file)
            })

            // Use the specific bulk endpoint
            // Note: need to make sure API client supports FormData or use fetch/axios direct
            // Assuming `api.post` handles it if we pass headers or just let axios detect
            await api.post(`/submissions/${examId}/submit-bulk-offline`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })

            router.push("/dashboard/student/results")
        } catch (err: any) {
            alert("Submission failed: " + (err.response?.data?.detail || err.message))
            setSubmitting(false)
        }
    }

    // --- RENDER FOR OFFLINE MODE ---
    if (isOffline) {
        return (
            <div className="max-w-4xl mx-auto space-y-8 pb-20">
                <div className="border-b border-slate-200 pb-4">
                    <h1 className="text-3xl font-bold">{exam.title}</h1>
                    <div className="flex items-center gap-3 mt-2">
                        <span className="bg-yellow-100 text-yellow-800 text-sm font-bold px-3 py-1 rounded-full border border-yellow-200">
                            OFFLINE EXAM
                        </span>
                        <div className={cn("flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full w-fit",
                            (timeLeft || 0) < 60 ? "bg-red-100 text-red-700 animate-pulse" : "bg-slate-100 text-slate-700"
                        )}>
                            <Clock className="w-4 h-4" />
                            <span>{timeLeft !== null ? formatTime(timeLeft) : "--:--"} Remaining</span>
                        </div>
                    </div>
                </div>

                {/* Instructions */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 text-blue-800">
                    <h3 className="font-bold text-lg mb-2">Instructions</h3>
                    <ul className="list-disc list-inside space-y-1 opacity-90">
                        <li>Read all questions below.</li>
                        <li>Write your answers on paper. Clearly label each answer (e.g. "Q1", "Answer 2").</li>
                        <li>Scan or take photos of ALL your pages.</li>
                        <li>Upload all pages at once in the section below.</li>
                        <li>The AI will automatically detect your answers and grade them.</li>
                    </ul>
                </div>

                {/* Question List (Read Only) */}
                <div className="space-y-6">
                    <h2 className="text-xl font-bold text-slate-900 border-b pb-2">Questions</h2>
                    {exam.questions.map((q, idx) => (
                        <div key={q.id} className="bg-white p-6 rounded-xl border border-slate-200">
                            <div className="flex justify-between mb-4">
                                <span className="font-bold text-slate-500">Q{idx + 1}</span>
                                <span className="text-sm font-medium bg-slate-100 px-2 py-1 rounded text-slate-600">{q.marks} Marks</span>
                            </div>
                            <p className="text-lg text-slate-800 leading-relaxed">{q.text}</p>
                        </div>
                    ))}
                </div>

                {/* Bulk Upload Area */}
                <div className="fixed bottom-0 left-0 lg:left-64 right-0 p-6 bg-white border-t border-slate-200 z-10 shadow-lg">
                    <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center gap-6">
                        <div className="flex-1 w-full">
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <Upload className="w-8 h-8 mb-3 text-slate-400" />
                                    <p className="mb-2 text-sm text-slate-500"><span className="font-semibold">Click to upload answer sheets</span></p>
                                    <p className="text-xs text-slate-500">PNG, JPG (Upload all pages)</p>
                                </div>
                                <input type="file" className="hidden" multiple accept="image/*" onChange={handleBulkFileChange} />
                            </label>
                            {bulkFiles.length > 0 && (
                                <div className="mt-2 text-sm text-emerald-600 font-medium text-center">
                                    {bulkFiles.length} files selected
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleBulkSubmit}
                            disabled={submitting || bulkFiles.length === 0}
                            className="w-full sm:w-auto px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-lg shadow-md disabled:opacity-50 min-w-[200px]"
                        >
                            {submitting ? (
                                <div className="flex items-center gap-2">
                                    <Loader2 className="animate-spin" /> Processing...
                                </div>
                            ) : "Submit All Pages"}
                        </button>
                    </div>
                </div>
                {/* Padding for fixed footer */}
                <div className="h-40"></div>
            </div>
        )
    }

    const question = exam.questions[currentQuestionIdx]
    const isLast = currentQuestionIdx === exam.questions.length - 1
    const currentAnswer = answers[question.id] || { text: "", file: null }

    return (
        <div className="max-w-3xl mx-auto space-y-8 pb-20">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div>
                    <h1 className="text-2xl font-bold">{exam.title}</h1>
                    <div className="flex items-center gap-3 mt-1">
                        <div className={cn("flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full w-fit",
                            (timeLeft || 0) < 60 ? "bg-red-100 text-red-700 animate-pulse" : "bg-slate-100 text-slate-700"
                        )}>
                            <Clock className="w-4 h-4" />
                            <span>{timeLeft !== null ? formatTime(timeLeft) : "--:--"} Remaining</span>
                        </div>

                        {isOffline && (
                            <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2 py-1 rounded-full border border-yellow-200">
                                OFFLINE EXAM
                            </span>
                        )}
                    </div>
                </div>
                <div className="text-right">
                    <span className="block text-sm font-medium text-slate-500">Question</span>
                    <span className="text-2xl font-bold">{currentQuestionIdx + 1} <span className="text-slate-300 text-lg">/ {exam.questions.length}</span></span>
                </div>
            </div>

            {/* Offline Mode Banner */}
            {isOffline && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex gap-3 text-blue-800">
                    <div className="p-2 bg-blue-100 rounded-lg h-fit">
                        <Upload className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="font-bold text-sm">Offline Submission Required</h3>
                        <p className="text-sm mt-1 opacity-90">
                            Please write your answer on paper. Take a clear photo and upload it using the button below.
                            Text input is optional (you can use it for transcripts or notes).
                        </p>
                    </div>
                </div>
            )}

            {/* Question Card */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 min-h-[400px] flex flex-col">
                <div className="flex justify-between mb-6">
                    <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">
                        {question.question_type}
                    </span>
                    <span className="font-medium text-slate-900">{question.marks} Marks</span>
                </div>

                <h2 className="text-xl font-medium text-slate-800 mb-8 leading-relaxed">
                    {(() => {
                        const { questionText } = parseQuestionText(question.text)
                        return questionText
                    })()}
                </h2>

                <div className="flex-1 space-y-4">

                    {/* Offline Mode: Upload is PRIMARY */}
                    {isOffline && (
                        <div className="mb-6 p-6 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 hover:bg-white hover:border-indigo-500 transition-all group text-center">
                            <input
                                type="file"
                                id="ans-upload-main"
                                className="hidden"
                                accept="image/*"
                                onChange={handleFileChange}
                            />
                            <label
                                htmlFor="ans-upload-main"
                                className="cursor-pointer flex flex-col items-center justify-center gap-2"
                            >
                                <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center text-indigo-600 group-hover:scale-110 transition-transform">
                                    <Upload className="w-6 h-6" />
                                </div>
                                <span className="font-bold text-slate-700">Upload Answer Photo</span>
                                <span className="text-xs text-slate-500">Click to select image</span>
                            </label>

                            {currentAnswer.file && (
                                <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-bold">
                                    <CheckCircle className="w-4 h-4" />
                                    {currentAnswer.file.name}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Text Input (Secondary for Offline, Primary for Online) */}
                    <div>
                        {!isOffline && <div className="text-sm font-medium text-slate-700 mb-2">Your Answer</div>}
                        {isOffline && <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Optional Transcript / Notes</div>}

                        {(() => {
                            const { isMCQ, options } = parseQuestionText(question.text)

                            if (isMCQ && !isOffline) {
                                return (
                                    <div className="space-y-3">
                                        {options.map((opt, idx) => (
                                            <label
                                                key={idx}
                                                className={cn(
                                                    "flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-all",
                                                    currentAnswer.text === opt
                                                        ? "bg-indigo-50 border-indigo-500 shadow-sm"
                                                        : "bg-white border-slate-200 hover:bg-slate-50 hover:border-slate-300"
                                                )}
                                            >
                                                <div className={cn(
                                                    "w-5 h-5 rounded-full border flex items-center justify-center transition-colors",
                                                    currentAnswer.text === opt
                                                        ? "border-indigo-600 bg-indigo-600"
                                                        : "border-slate-300 bg-white"
                                                )}>
                                                    {currentAnswer.text === opt && <div className="w-2 h-2 rounded-full bg-white" />}
                                                </div>
                                                <input
                                                    type="radio"
                                                    name={`q-${question.id}`}
                                                    value={opt}
                                                    checked={currentAnswer.text === opt}
                                                    onChange={() => handleTextChange(opt)}
                                                    className="hidden"
                                                />
                                                <span className="text-slate-700">{opt}</span>
                                            </label>
                                        ))}
                                    </div>
                                )
                            }

                            return (
                                <textarea
                                    className={cn(
                                        "w-full p-4 rounded-lg border  focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none",
                                        isOffline ? "h-24 bg-slate-50 border-slate-200 text-sm" : "h-48 bg-white border-slate-300"
                                    )}
                                    placeholder={isOffline ? "Optional: Type any notes or transcript here..." : "Type your answer here..."}
                                    value={currentAnswer.text}
                                    onChange={(e) => handleTextChange(e.target.value)}
                                />
                            )
                        })()}
                    </div>

                    {/* Show standard upload button ONLY if NOT offline (since offline has the big one above) */}
                    {!isOffline && (
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <input
                                    type="file"
                                    id="ans-upload"
                                    className="hidden"
                                    accept="image/*"
                                    onChange={handleFileChange}
                                />
                                <label
                                    htmlFor="ans-upload"
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-md text-sm font-medium hover:bg-slate-50 cursor-pointer text-slate-600"
                                >
                                    <Upload className="w-4 h-4" />
                                    Upload Handwritten Photo
                                </label>
                            </div>
                            {currentAnswer.file && <span className="text-xs text-emerald-600 font-medium flex items-center gap-1"><CheckCircle className="w-3 h-3" /> {currentAnswer.file.name} attached</span>}
                        </div>
                    )}
                </div>
            </div>

            {/* Footer Navigation */}
            <div className="fixed bottom-0 left-0 lg:left-64 right-0 p-4 bg-white border-t border-slate-200 flex justify-between items-center z-10">
                <button
                    onClick={() => setCurrentQuestionIdx(prev => Math.max(0, prev - 1))}
                    disabled={currentQuestionIdx === 0}
                    className="px-6 py-2 rounded-lg text-slate-600 font-medium hover:bg-slate-100 disabled:opacity-50"
                >
                    <ArrowLeft className="w-5 h-5 inline mr-2" />
                    Previous
                </button>

                {isLast ? (
                    <button
                        onClick={() => handleSubmit(false)}
                        disabled={submitting}
                        className="px-8 py-2 rounded-lg bg-emerald-600 text-white font-bold hover:bg-emerald-700 shadow-lg shadow-emerald-200 disabled:opacity-70"
                    >
                        {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : "Submit Exam"}
                    </button>
                ) : (
                    <button
                        onClick={() => setCurrentQuestionIdx(prev => Math.min(exam.questions.length - 1, prev + 1))}
                        className="px-6 py-2 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800"
                    >
                        Next
                        <ArrowRight className="w-5 h-5 inline ml-2" />
                    </button>
                )}
            </div>
        </div>
    )
}
