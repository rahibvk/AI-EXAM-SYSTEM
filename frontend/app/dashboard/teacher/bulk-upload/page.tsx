"use client"

import { useState, useEffect } from "react"
import { UploadCloud, CheckCircle, AlertCircle, FileText, Loader2 } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

export default function BulkUploadPage() {
    const [courses, setCourses] = useState<any[]>([])
    const [exams, setExams] = useState<any[]>([])
    const [selectedCourse, setSelectedCourse] = useState("")
    const [selectedExam, setSelectedExam] = useState("")
    const [files, setFiles] = useState<File[]>([])
    const [uploading, setUploading] = useState(false)
    const [results, setResults] = useState<any[]>([])

    // Fetch Courses on load
    useEffect(() => {
        const fetchCourses = async () => {
            try {
                const res = await api.get("/courses")
                setCourses(res.data)
            } catch (error) {
                console.error("Failed to load courses", error)
            }
        }
        fetchCourses()
    }, [])

    // Fetch Exams when Course selected
    useEffect(() => {
        const fetchExams = async () => {
            if (!selectedCourse) {
                setExams([])
                return
            }
            try {
                const res = await api.get(`/exams/course/${selectedCourse}`)
                // Filter for offline exams only? Or all? User said "offline exam", but maybe online too for handwritten?
                // Let's allow all for flexibility, or filter if 'mode' is strictly checked.
                setExams(res.data)
            } catch (error) {
                console.error("Failed to load exams", error)
            }
        }
        fetchExams()
    }, [selectedCourse])

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles(Array.from(e.target.files))
        }
    }

    const handleUpload = async () => {
        if (!selectedExam || files.length === 0) return

        setUploading(true)
        setResults([])

        const formData = new FormData()
        files.forEach((file) => {
            formData.append("files", file)
        })

        try {
            const res = await api.post(`/exams/${selectedExam}/bulk-upload`, formData, {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            })
            setResults(res.data)
            setFiles([]) // Clear files on success
        } catch (error: any) {
            alert("Upload failed: " + (error.response?.data?.detail || error.message))
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Bulk Exam Correction</h1>
                <p className="text-slate-500">Upload scanned answer sheets. AI will identify the student and grade the answers.</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8">
                {/* Left Panel: Upload Config */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                        <h2 className="font-semibold text-lg flex items-center gap-2">
                            <UploadCloud className="w-5 h-5 text-indigo-600" />
                            Upload Papers
                        </h2>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Select Course</label>
                                <select
                                    className="w-full h-10 rounded-md border border-slate-200 px-3 py-2 text-sm"
                                    value={selectedCourse}
                                    onChange={(e) => setSelectedCourse(e.target.value)}
                                >
                                    <option value="">-- Choose Course --</option>
                                    {courses.map((c: any) => (
                                        <option key={c.id} value={c.id}>{c.title}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Select Exam</label>
                                <select
                                    className="w-full h-10 rounded-md border border-slate-200 px-3 py-2 text-sm"
                                    value={selectedExam}
                                    onChange={(e) => setSelectedExam(e.target.value)}
                                    disabled={!selectedCourse}
                                >
                                    <option value="">-- Choose Exam --</option>
                                    {exams.map((e: any) => (
                                        <option key={e.id} value={e.id}>{e.title}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="border-2 border-dashed border-slate-200 rounded-lg p-8 text-center hover:bg-slate-50 transition-colors relative">
                            <input
                                type="file"
                                multiple
                                accept="image/*,.pdf"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            />
                            <UploadCloud className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                            <p className="text-sm font-medium text-slate-700">
                                {files.length > 0 ? `${files.length} files selected` : "Drag files here or click to browse"}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">Supports Images (JPG, PNG) and PDF</p>
                        </div>

                        {files.length > 0 && (
                            <div className="max-h-32 overflow-y-auto space-y-2">
                                {files.map((f, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm text-slate-600 bg-slate-50 p-2 rounded">
                                        <FileText className="w-4 h-4" />
                                        <span className="truncate">{f.name}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={uploading || !selectedExam || files.length === 0}
                            className="w-full h-11 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                "Start Bulk Processing"
                            )}
                        </button>
                    </div>
                </div>

                {/* Right Panel: Results */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-full min-h-[400px] flex flex-col">
                        <h2 className="font-semibold text-lg mb-4">Processing Results</h2>

                        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                            {results.length === 0 && !uploading && (
                                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                                    <FileText className="w-12 h-12 mb-3 opacity-20" />
                                    <p>Results will appear here</p>
                                </div>
                            )}

                            {uploading && (
                                <div className="space-y-4 animate-pulse">
                                    {[1, 2, 3].map((i) => (
                                        <div key={i} className="h-16 bg-slate-100 rounded-lg"></div>
                                    ))}
                                </div>
                            )}

                            {results.map((res, idx) => (
                                <div
                                    key={idx}
                                    className={cn(
                                        "p-4 rounded-lg border flex items-start justify-between",
                                        res.status === 'success' ? "bg-emerald-50 border-emerald-100" : "bg-red-50 border-red-100"
                                    )}
                                >
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            {res.status === 'success' ? (
                                                <CheckCircle className="w-4 h-4 text-emerald-600" />
                                            ) : (
                                                <AlertCircle className="w-4 h-4 text-red-600" />
                                            )}
                                            <span className="font-medium text-slate-900">{res.filename}</span>
                                        </div>
                                        {res.status === 'success' ? (
                                            <div className="text-sm text-emerald-700">
                                                Identified: <span className="font-bold">{res.student}</span>
                                                <br />
                                                Assigned Score: {res.score}
                                            </div>
                                        ) : (
                                            <div className="text-sm text-red-600">
                                                Error: {res.error}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
