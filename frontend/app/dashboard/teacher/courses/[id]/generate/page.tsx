"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, Sparkles, Save, ArrowLeft, RefreshCw, CheckCircle } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"
import { parseQuestionText } from "@/lib/examUtils"

interface GeneratedQuestion {
    text: string
    question_type: string
    marks: number
    model_answer: string
}

export default function GenerateExamPage() {
    const params = useParams()
    const router = useRouter()
    const courseId = params.id
    console.log("Generate Page Mounted, CourseID:", courseId)

    const [step, setStep] = useState<"config" | "preview">("config")
    const [loading, setLoading] = useState(false)
    const [questions, setQuestions] = useState<GeneratedQuestion[]>([])
    const [examTitle, setExamTitle] = useState("")
    const [materials, setMaterials] = useState<any[]>([])
    const [selectedMaterials, setSelectedMaterials] = useState<number[]>([])

    // Form for configuration
    const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm({
        defaultValues: {
            difficulty: "Medium",
            subjective_count: 3,
            objective_count: 2,
        }
    })

    // Fetch materials on mount
    useEffect(() => {
        const fetchMaterials = async () => {
            try {
                const res = await api.get(`/courses/${courseId}`)
                setMaterials(res.data.materials || [])
            } catch (err) {
                console.error(err)
            }
        }
        if (courseId) fetchMaterials()
    }, [courseId])

    const handleMaterialToggle = (id: number) => {
        setSelectedMaterials(prev =>
            prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
        )
    }

    // 1. Generate Questions
    const onGenerate = async (data: any) => {
        setLoading(true)
        try {
            const res = await api.post("/exams/generate", {
                course_id: Number(courseId),
                // topic removed
                difficulty: data.difficulty,
                subjective_count: Number(data.subjective_count),
                objective_count: Number(data.objective_count),
                total_marks: Number(data.total_marks || 100),
                material_ids: selectedMaterials.length > 0 ? selectedMaterials : undefined
            })
            setQuestions(res.data)
            setExamTitle(`Exam for ${new Date().toLocaleDateString()}`)
            setStep("preview")
        } catch (err: any) {
            alert("Generation failed: " + (err.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    // State for Exam Settings in Preview
    const [examSettings, setExamSettings] = useState({
        mode: "online",
        startTime: "",
        endTime: "",
        duration: 60,
        passingMarks: 40 // Default 40%
    })

    // 2. Save Exam
    const onSave = async () => {
        setLoading(true)
        try {
            // Check for Offline Mode -> PDF Download
            if (examSettings.mode === 'offline') {
                try {
                    const { jsPDF } = await import('jspdf')
                    const doc = new jsPDF()

                    // Title
                    doc.setFontSize(22)
                    doc.text(examTitle, 20, 20)

                    doc.setFontSize(12)
                    doc.text(`Duration: ${examSettings.duration} Minutes`, 20, 30)
                    doc.text(`Total Marks: ${questions.reduce((sum, q) => sum + q.marks, 0)} (Pass: ${examSettings.passingMarks})`, 20, 36)

                    doc.line(20, 40, 190, 40)

                    // ... rest of PDF logic (unchanged essentially, just added pass marks to header)
                    let y = 50
                    questions.forEach((q, i) => {
                        if (y > 270) {
                            doc.addPage()
                            y = 20
                        }

                        doc.setFontSize(12)
                        doc.setFont("helvetica", "bold")
                        doc.text(`Q${i + 1}. [${q.marks} Marks]`, 20, y)

                        doc.setFont("helvetica", "normal")
                        const splitText = doc.splitTextToSize(q.text, 170)
                        doc.text(splitText, 20, y + 6)

                        y += (splitText.length * 5) + 20
                    })

                    doc.save(`${examTitle.replace(/\s+/g, '_')}_Offline.pdf`)

                } catch (pdfErr) {
                    console.error("PDF Gen Failed", pdfErr)
                    alert("Failed to generate PDF, but saving exam record.")
                }
            }

            await api.post("/exams", {
                title: examTitle,
                description: "AI Generated Exam",
                course_id: Number(courseId),
                questions: questions,
                total_marks: questions.reduce((sum, q) => sum + q.marks, 0),
                duration_minutes: Number(examSettings.duration),
                start_time: examSettings.startTime ? new Date(examSettings.startTime).toISOString() : null,
                end_time: examSettings.endTime ? new Date(examSettings.endTime).toISOString() : null,
                mode: examSettings.mode,
                passing_marks: Number(examSettings.passingMarks)
            })
            router.push(`/dashboard/teacher/courses/${courseId}`)
        } catch (err: any) {
            alert("Save failed: " + (err.response?.data?.detail || err.message))
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-slate-500" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">AI Exam Generator</h1>
                    <p className="text-slate-500">Create a new exam instantly from your course materials.</p>
                </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-8">

                {/* Left Config Panel */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-slate-900 font-semibold">
                            <Sparkles className="w-5 h-5 text-purple-500" />
                            <span>Configuration</span>
                        </div>

                        <form onSubmit={handleSubmit(onGenerate)} className="space-y-4">

                            {/* Material Selection */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Select Materials (Optional)</label>
                                <div className="max-h-32 overflow-y-auto border border-slate-200 rounded-md p-2 space-y-2">
                                    {materials.map((m) => (
                                        <div key={m.id} className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                id={`mat-${m.id}`}
                                                checked={selectedMaterials.includes(m.id)}
                                                onChange={() => handleMaterialToggle(m.id)}
                                                className="rounded border-slate-300 text-purple-600 focus:ring-purple-600"
                                            />
                                            <label htmlFor={`mat-${m.id}`} className="text-sm text-slate-700 truncate cursor-pointer select-none">
                                                {m.title}
                                            </label>
                                        </div>
                                    ))}
                                    {materials.length === 0 && <p className="text-xs text-slate-400">No materials found.</p>}
                                </div>
                                <p className="text-xs text-slate-500">Leave unchecked to use all materials.</p>
                            </div>

                            <div className="space-y-2">
                                {/* Topic Input Removed */}
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Difficulty</label>
                                    <select
                                        {...register("difficulty")}
                                        className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 bg-transparent"
                                    >
                                        <option value="Easy">Easy</option>
                                        <option value="Medium">Medium</option>
                                        <option value="Hard">Hard</option>
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Total Marks</label>
                                    <input
                                        type="number"
                                        {...register("total_marks", { value: 100 })}
                                        className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 bg-transparent"
                                        min={10} max={1000}
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Subjective Qs</label>
                                    <input
                                        type="number"
                                        {...register("subjective_count")}
                                        className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 bg-transparent"
                                        min={0} max={10}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">MCQs</label>
                                    <input
                                        type="number"
                                        {...register("objective_count")}
                                        className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 bg-transparent"
                                        min={0} max={10}
                                    />
                                </div>
                            </div>

                            <button
                                disabled={loading && step === 'config'}
                                className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:opacity-90 h-10 px-4 py-2 transition-all mt-4"
                            >
                                {loading && step === 'config' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
                                Generate
                            </button>
                        </form>
                    </div>
                </div>

                {/* Right Preview Panel */}
                <div className="lg:col-span-2">
                    {loading && step === 'config' ? (
                        <div className="h-full flex flex-col items-center justify-center min-h-[400px] bg-slate-50 rounded-xl border-2 border-dashed border-slate-200">
                            <Loader2 className="w-10 h-10 animate-spin text-purple-500 mb-4" />
                            <h3 className="text-lg font-medium text-slate-700">Analyzing Course Materials...</h3>
                            <p className="text-slate-500">Extracting context and drafting questions.</p>
                        </div>
                    ) : step === 'preview' ? (
                        <div className="space-y-6">
                            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-lg font-bold">Preview Exam</h2>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setStep('config')}
                                            className="p-2 text-slate-500 hover:bg-slate-50 rounded-md"
                                            title="Regenerate"
                                        >
                                            <RefreshCw className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                    <div>
                                        <label className="text-sm font-medium">Exam Title</label>
                                        <input
                                            value={examTitle}
                                            onChange={(e) => setExamTitle(e.target.value)}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-lg font-bold focus:ring-2 focus:ring-slate-900 bg-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Exam Mode</label>
                                        <select
                                            value={examSettings.mode}
                                            onChange={(e) => setExamSettings({ ...examSettings, mode: e.target.value })}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 bg-transparent"
                                        >
                                            <option value="online">Online (Auto-Evaluation)</option>
                                            <option value="offline">Offline (PDF Download)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Duration (Minutes)</label>
                                        <input
                                            type="number"
                                            value={examSettings.duration}
                                            onChange={(e) => setExamSettings({ ...examSettings, duration: Number(e.target.value) })}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 bg-transparent"
                                            min="1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Start Time</label>
                                        <input
                                            type="datetime-local"
                                            value={examSettings.startTime}
                                            onChange={(e) => setExamSettings({ ...examSettings, startTime: e.target.value })}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 bg-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">End Time</label>
                                        <input
                                            type="datetime-local"
                                            value={examSettings.endTime}
                                            onChange={(e) => setExamSettings({ ...examSettings, endTime: e.target.value })}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 bg-transparent"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium">Passing Marks</label>
                                        <input
                                            type="number"
                                            value={examSettings.passingMarks}
                                            onChange={(e) => setExamSettings({ ...examSettings, passingMarks: Number(e.target.value) })}
                                            className="flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 bg-transparent border-emerald-200 focus:border-emerald-500"
                                            min="0"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <AnimatePresence>
                                        {questions.map((q, i) => {
                                            const { isMCQ, questionText, options } = parseQuestionText(q.text)

                                            return (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.1 }}
                                                    className="p-4 bg-slate-50 rounded-lg border border-slate-200"
                                                >
                                                    <div className="flex justify-between items-start mb-2">
                                                        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Question {i + 1}</span>
                                                        <span className="text-xs font-medium bg-white px-2 py-1 rounded border border-slate-200">{q.marks} Marks</span>
                                                    </div>
                                                    <p className="text-slate-900 font-medium mb-3 whitespace-pre-wrap">{questionText}</p>

                                                    {isMCQ && (
                                                        <div className="mb-4 pl-4 space-y-1">
                                                            {options.map((opt, idx) => (
                                                                <div key={idx} className="flex items-center gap-2 text-sm text-slate-700">
                                                                    <div className="w-4 h-4 rounded-full border border-slate-300 flex items-center justify-center text-[10px] text-slate-400">
                                                                        {String.fromCharCode(65 + idx)}
                                                                    </div>
                                                                    <span>{opt}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}

                                                    <div className="bg-white p-3 rounded border border-slate-100/50">
                                                        <p className="text-xs text-emerald-600 font-semibold mb-1">Model Answer:</p>
                                                        <p className="text-sm text-slate-600">{q.model_answer}</p>
                                                    </div>
                                                </motion.div>
                                            )
                                        })}
                                    </AnimatePresence>
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <button
                                    onClick={onSave}
                                    disabled={loading}
                                    className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-emerald-600 text-white hover:bg-emerald-700 h-11 px-8 shadow-sm transition-colors"
                                >
                                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                    Save & Publish Exam
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center min-h-[400px] bg-white rounded-xl border border-slate-100">
                            <div className="w-16 h-16 bg-purple-50 text-purple-500 rounded-full flex items-center justify-center mb-4">
                                <Sparkles className="w-8 h-8" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-900">Ready to Generate</h3>
                            <p className="text-slate-500 max-w-sm text-center mt-2">
                                Configure the settings on the left to generate a custom exam using your course materials.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
