"use client"

import { useEffect, useState, use } from "react"
import Link from "next/link"
import { ArrowLeft, Upload, FileText, Trash2, Loader2, Sparkles } from "lucide-react"
import api from "@/lib/api"
import { useParams, useRouter } from "next/navigation"

interface Course {
    id: number
    title: string
    code: string
    description: string
    materials: any[]
}

export default function CourseDetailPage() {
    const router = useRouter()
    const params = useParams()
    const id = params.id

    const [course, setCourse] = useState<Course | null>(null)
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)

    const fetchCourse = async () => {
        try {
            const res = await api.get(`/courses/${id}`)
            setCourse(res.data) // Assuming get_course details endpoint returns this structure
            // If endpoint doesn't return materials, might need separate fetch
        } catch (error) {
            console.error("Failed to fetch course values")
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        if (id) fetchCourse()
    }, [id])

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.length) return

        setUploading(true)
        const file = e.target.files[0]
        const formData = new FormData()
        formData.append("file", file)
        formData.append("title", file.name) // Default title to filename for now

        try {
            await api.post(`/courses/${id}/materials`, formData, {
                headers: { "Content-Type": "multipart/form-data" }
            })
            // Refresh
            fetchCourse()
        } catch (err: any) {
            alert("Upload failed: " + (err.response?.data?.detail || err.message))
        } finally {
            setUploading(false)
        }
    }

    const handleGenerateExam = () => {
        // Mock navigation to generator
        router.push(`/dashboard/teacher/courses/${id}/generate`)
    }

    if (loading) return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin" /></div>
    if (!course) return <div>Course not found</div>

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/dashboard/teacher/courses" className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-slate-500" />
                </Link>
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold tracking-tight">{course.title}</h1>
                        <span className="bg-slate-100 text-slate-600 px-2 py-1 rounded text-sm font-mono">{course.code}</span>
                    </div>
                    <p className="text-slate-500 mt-1">{course.description}</p>
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                {/* Main Content: Materials */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold">Course Materials</h2>
                        <div className="relative">
                            <input
                                type="file"
                                id="file-upload"
                                className="hidden"
                                accept=".pdf,.txt"
                                onChange={handleFileUpload}
                                disabled={uploading}
                            />
                            <label
                                htmlFor="file-upload"
                                className={`inline-flex items-center gap-2 px-4 py-2 rounded-md bg-white border border-slate-200 text-sm font-medium hover:bg-slate-50 cursor-pointer shadow-sm ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                                {uploading ? "Processing..." : "Upload PDF/Text"}
                            </label>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {course.materials?.length === 0 ? (
                            <div className="text-center py-10 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
                                <Upload className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                                <p className="text-slate-500">No materials uploaded yet.</p>
                                <p className="text-xs text-slate-400">Upload documents to enable AI features.</p>
                            </div>
                        ) : (
                            course.materials?.map((mat: any) => (
                                <div key={mat.id} className="flex items-center p-4 bg-white border border-slate-200 rounded-lg group hover:border-blue-300 transition-colors">
                                    <div className="p-2 bg-blue-50 text-blue-600 rounded mr-4">
                                        <FileText className="w-5 h-5" />
                                    </div>
                                    <div className="flex-1">
                                        <h4 className="font-medium text-slate-900">{mat.title}</h4>
                                        <p className="text-xs text-slate-500">
                                            {mat.file_type || "Document"} • Added recently
                                        </p>
                                    </div>
                                    <button className="text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Sidebar: AI Actions */}
                <div className="space-y-6">
                    <div className="p-6 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl text-white shadow-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Sparkles className="w-5 h-5 text-yellow-400" />
                            <h3 className="font-semibold text-lg">AI Actions</h3>
                        </div>
                        <p className="text-slate-300 text-sm mb-6">
                            Use your uploaded materials to generate content automatically.
                        </p>

                        <button
                            onClick={handleGenerateExam}
                            className="w-full py-2.5 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg font-medium text-sm transition-colors mb-2"
                        >
                            Generate Exam
                        </button>
                        <button className="w-full py-2.5 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg font-medium text-sm transition-colors">
                            Create Flashcards
                        </button>
                    </div>

                    <div className="p-6 bg-white border border-slate-200 rounded-xl">
                        <h3 className="font-semibold mb-4">Exam History</h3>
                        <p className="text-sm text-slate-500">No exams created yet.</p>
                    </div>
                </div>
            </div>
        </div>
    )
}
