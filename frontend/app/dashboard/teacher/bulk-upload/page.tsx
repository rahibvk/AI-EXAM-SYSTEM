"use client"

import { useState, useEffect } from "react"
import { UploadCloud, CheckCircle, AlertCircle, FileText, Loader2, Search, User } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"

export default function BulkUploadPage() {
    const [courses, setCourses] = useState<any[]>([])
    const [exams, setExams] = useState<any[]>([])
    const [selectedCourse, setSelectedCourse] = useState("")
    const [selectedExam, setSelectedExam] = useState("")
    const [files, setFiles] = useState<File[]>([])
    const [uploading, setUploading] = useState(false)
    const [results, setResults] = useState<any[]>([])

    // Manual Assignment State
    const [assignIndex, setAssignIndex] = useState<number | null>(null)
    const [searchQuery, setSearchQuery] = useState("")
    const [searchResults, setSearchResults] = useState<any[]>([])

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

    const handleConfirm = async (res: any, index: number) => {
        if (!res.student) return

        // Optimistic update
        const newResults = [...results]
        newResults[index].confirming = true
        setResults(newResults)

        try {
            const confirmRes = await api.post(`/exams/${selectedExam}/confirm-upload`, {
                student_id: res.student.id,
                answers: res.extracted_data.answers
            })

            // Update with success result
            newResults[index] = { ...confirmRes.data, filename: res.filename, status: 'success' }
            setResults([...newResults])

        } catch (error: any) {
            alert("Confirmation failed")
            newResults[index].confirming = false
            setResults([...newResults])
        }
    }

    const handleSearch = async (query: string) => {
        setSearchQuery(query)
        if (query.length < 2) {
            setSearchResults([])
            return
        }
        try {
            const res = await api.get(`/users/search?q=${query}`)
            setSearchResults(res.data)
        } catch (e) {
            console.error("Search failed")
        }
    }

    const assignStudent = (student: any) => {
        if (assignIndex === null) return

        const newResults = [...results]
        newResults[assignIndex].student = {
            id: student.id,
            name: student.full_name,
            email: student.email
        }
        newResults[assignIndex].status = 'ready_for_review' // Move to ready state
        setResults(newResults)

        // Reset
        setAssignIndex(null)
        setSearchQuery("")
        setSearchResults([])
    }

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Bulk Exam Correction</h1>
                <p className="text-slate-500">Upload scanned answer sheets. AI will identify the student and wait for your confirmation before grading.</p>
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
                                "Start Analysis"
                            )}
                        </button>
                    </div>
                </div>

                {/* Right Panel: Results */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-full min-h-[400px] flex flex-col">
                        <h2 className="font-semibold text-lg mb-4">Results</h2>

                        <div className="flex-1 overflow-y-auto space-y-6 pr-2 custom-scrollbar">
                            {/* Unidentified Section */}
                            {results.some(r => r.status === 'action_required') && (
                                <div className="space-y-3">
                                    <h3 className="text-sm font-bold text-red-600 uppercase flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" />
                                        Action Required ({results.filter(r => r.status === 'action_required').length})
                                    </h3>
                                    {results.map((res, idx) => res.status === 'action_required' && (
                                        <div key={idx} className="p-4 rounded-lg border border-red-200 bg-red-50 flex flex-col gap-3">
                                            <div className="flex items-center justify-between">
                                                <span className="font-medium text-slate-900 truncate">{res.filename}</span>
                                                <span className="text-xs text-red-600 font-bold bg-white px-2 py-1 rounded border border-red-100">Student Not Found</span>
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => setAssignIndex(idx)}
                                                    className="w-full py-2 bg-white border border-red-200 text-red-600 rounded-md text-sm font-medium hover:bg-red-100 flex items-center justify-center gap-2"
                                                >
                                                    <Search className="w-4 h-4" />
                                                    Find & Assign Student
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Identified Section */}
                            <div className="space-y-3">
                                {results.some(r => r.status !== 'action_required') && (
                                    <h3 className="text-sm font-bold text-slate-500 uppercase">Ready for Grading</h3>
                                )}

                                {results.map((res, idx) => res.status !== 'action_required' && (
                                    <div
                                        key={idx}
                                        className={cn(
                                            "p-4 rounded-lg border flex flex-col gap-2 transition-all",
                                            res.status === 'success' ? "bg-emerald-50 border-emerald-100" : "bg-blue-50 border-blue-100"
                                        )}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-2">
                                                {res.status === 'success' ? (
                                                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                                                ) : (
                                                    <AlertCircle className="w-5 h-5 text-blue-600" />
                                                )}
                                                <div>
                                                    <span className="font-semibold text-slate-900 block">{res.filename}</span>
                                                    {res.status === 'ready_for_review' && (
                                                        <span className="text-xs text-blue-600 font-medium">Ready for Confirmation</span>
                                                    )}
                                                    {res.status === 'success' && (
                                                        <span className="text-xs text-emerald-600 font-medium">Grading Complete</span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="pl-7">
                                            {res.status === 'ready_for_review' && (
                                                <div className="space-y-3">
                                                    <div className="text-sm text-slate-700 bg-white/50 p-2 rounded border border-blue-100">
                                                        <div className="space-y-1">
                                                            <p>Student: <span className="font-bold text-slate-900">{res.student?.name}</span> <span className="text-slate-500">({res.student?.email})</span></p>
                                                            <p className="text-xs text-slate-500">
                                                                {res.extracted_data?.answers ? Object.keys(res.extracted_data.answers).length : 0} Answers Captured
                                                            </p>
                                                        </div>
                                                    </div>

                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleConfirm(res, idx)}
                                                            disabled={res.confirming}
                                                            className="flex-1 text-xs bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                                                        >
                                                            {res.confirming && <Loader2 className="w-3 h-3 animate-spin" />}
                                                            {res.confirming ? "Evaluating..." : "Confirm & Evaluate"}
                                                        </button>
                                                        <button
                                                            onClick={() => setAssignIndex(idx)}
                                                            className="px-2 py-2 bg-white border border-blue-200 text-blue-600 rounded-md hover:bg-blue-50"
                                                            title="Change Student"
                                                        >
                                                            <User className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>
                                            )}

                                            {res.status === 'success' && (
                                                <div className="text-sm text-emerald-700">
                                                    Student: <span className="font-bold">{res.student?.name || res.student}</span>
                                                    <br />
                                                    Assigned Score: <span className="font-bold">{res.score}</span>
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

            {/* Manual Assignment Modal */}
            <Dialog open={assignIndex !== null} onOpenChange={() => setAssignIndex(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Assign Student to Paper</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 pt-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Search Student</label>
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <input
                                    className="w-full pl-9 pr-4 py-2 border rounded-md"
                                    placeholder="Search name or email..."
                                    value={searchQuery}
                                    onChange={(e) => handleSearch(e.target.value)}
                                    autoFocus
                                />
                            </div>
                        </div>

                        <div className="max-h-60 overflow-y-auto border rounded-md divide-y">
                            {searchResults.length === 0 ? (
                                <div className="p-4 text-center text-sm text-slate-500">
                                    {searchQuery.length < 2 ? "Type to search..." : "No students found."}
                                </div>
                            ) : (
                                searchResults.map(s => (
                                    <button
                                        key={s.id}
                                        onClick={() => assignStudent(s)}
                                        className="w-full text-left px-4 py-3 hover:bg-slate-50 flex flex-col gap-1 transition-colors"
                                    >
                                        <span className="font-medium text-sm text-slate-900">{s.full_name}</span>
                                        <span className="text-xs text-slate-500">{s.email}</span>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    )
}
