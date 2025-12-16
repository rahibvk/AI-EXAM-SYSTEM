"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, ArrowRight, ArrowLeft, Upload, CheckCircle, Clock } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

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

    useEffect(() => {
        const fetchExam = async () => {
            try {
                const res = await api.get(`/exams/${examId}`)
                const examData = res.data
                setExam(examData)

                // Calculate Time Left
                // Logic: 
                // 1. Duration provided in minutes (e.g. 10 mins).
                // 2. But strict EndTime might cut it short.
                // 3. We use the backend response (which implies we are inside the valid window).
                // Let's rely on examData.duration_minutes first, but checking against end_time would be better strict logic.
                // For MVP, if backend let us in, we start the timer based on duration.

                // Robust Calc:
                // If end_time exists: timeLeft = min(duration, end_time - now)
                // But for simplicity and to match user request "10 mins exam", we just use duration.
                // Ideally backend sends "seconds_remaining".

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
        // Prevent double submission
        if (submitting) return;
        alert("Time is up! Your exam is being submitted automatically.")
        handleSubmit(true) // Pass flag to skip confirmation
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
                    answer_file_path: null
                }))
            }

            await api.post("/submissions/submit", payload)

            // Success
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

    const question = exam.questions[currentQuestionIdx]
    const isLast = currentQuestionIdx === exam.questions.length - 1
    const currentAnswer = answers[question.id] || { text: "", file: null }

    return (
        <div className="max-w-3xl mx-auto space-y-8 pb-20">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div>
                    <h1 className="text-2xl font-bold">{exam.title}</h1>
                    <div className={cn("flex items-center gap-2 text-sm mt-1 font-medium px-3 py-1 rounded-full w-fit",
                        (timeLeft || 0) < 60 ? "bg-red-100 text-red-700 animate-pulse" : "bg-slate-100 text-slate-700"
                    )}>
                        <Clock className="w-4 h-4" />
                        <span>{timeLeft !== null ? formatTime(timeLeft) : "--:--"} Remaining</span>
                    </div>
                </div>
                <div className="text-right">
                    <span className="block text-sm font-medium text-slate-500">Question</span>
                    <span className="text-2xl font-bold">{currentQuestionIdx + 1} <span className="text-slate-300 text-lg">/ {exam.questions.length}</span></span>
                </div>
            </div>

            {/* Question Card */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 min-h-[400px] flex flex-col">
                <div className="flex justify-between mb-6">
                    <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">
                        {question.question_type}
                    </span>
                    <span className="font-medium text-slate-900">{question.marks} Marks</span>
                </div>

                <h2 className="text-xl font-medium text-slate-800 mb-8 leading-relaxed">
                    {question.text}
                </h2>

                <div className="flex-1 space-y-4">
                    <textarea
                        className="w-full h-48 p-4 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none bg-slate-50"
                        placeholder="Type your answer here..."
                        value={currentAnswer.text}
                        onChange={(e) => handleTextChange(e.target.value)}
                    />

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
                        onClick={handleSubmit}
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
