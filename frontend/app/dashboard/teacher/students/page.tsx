"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Search, Mail, User, Plus, BookOpen, X, Check } from "lucide-react"
import { useRouter } from "next/navigation"
import api from "@/lib/api"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

export default function StudentsListPage() {
    const router = useRouter()
    const [students, setStudents] = useState<any[]>([])
    const [courses, setCourses] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState("")

    // Enroll Modal State
    const [isEnrollOpen, setIsEnrollOpen] = useState(false)
    const [enrollEmail, setEnrollEmail] = useState("")
    const [enrollCourseId, setEnrollCourseId] = useState("")
    const [enrollLoading, setEnrollLoading] = useState(false)

    // Manage Modal State
    const [manageStudent, setManageStudent] = useState<any>(null)
    const [manageLoading, setManageLoading] = useState(false)

    // Search State
    const [searchQuery, setSearchQuery] = useState("")
    const [searchResults, setSearchResults] = useState<any[]>([])
    const [selectedStudent, setSelectedStudent] = useState<any>(null)

    const handleSearch = async (query: string) => {
        if (query.length < 2) {
            setSearchResults([])
            return
        }
        try {
            const res = await api.get(`/users/search?q=${query}`)
            setSearchResults(res.data)
        } catch (e) {
            console.error("Search failed", e)
        }
    }

    const fetchData = async () => {
        setLoading(true)
        try {
            // 1. Fetch Teacher's Courses
            const coursesRes = await api.get("/courses/my-courses")
            const coursesData = coursesRes.data
            setCourses(coursesData)

            // 2. Fetch Students per Course
            const validStudentsMap = new Map()

            // Helper to add student to map
            const addInfo = (s: any, course: any) => {
                if (!validStudentsMap.has(s.id)) {
                    validStudentsMap.set(s.id, { ...s, enrolledCourses: [] })
                }
                if (course) {
                    const entry = validStudentsMap.get(s.id)
                    // Check duplicates
                    if (!entry.enrolledCourses.find((c: any) => c.id === course.id)) {
                        entry.enrolledCourses.push(course)
                    }
                }
            }

            // Fetch enrolled students for each course
            await Promise.all(coursesData.map(async (c: any) => {
                try {
                    const sRes = await api.get(`/courses/${c.id}/students`)
                    sRes.data.forEach((s: any) => addInfo(s, c))
                } catch (e) {
                    console.error(`Failed to load students for course ${c.id}`, e)
                }
            }))

            // 3. Optional: Fetch legacy students (with submissions but maybe no enrollment)
            // If we want to support them, we can merge. 
            // For now, let's stick to explicit enrollments as that's the new source of truth.
            // But if user wants to manage them, they should probably be added.
            // Let's fetch "my-students" just in case and show them with empty courses if not enrolled.
            try {
                const legacyRes = await api.get("/users/my-students")
                legacyRes.data.forEach((s: any) => addInfo(s, null))
            } catch (e) { console.error("Legacy fetch failed", e) }

            setStudents(Array.from(validStudentsMap.values()))

        } catch (error) {
            console.error("Failed to fetch data", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [])

    const handleEnroll = async () => {
        if (!enrollEmail || !enrollCourseId) return
        setEnrollLoading(true)
        try {
            await api.post(`/courses/${enrollCourseId}/students`, { email: enrollEmail })
            alert("Student enrolled successfully!")
            setEnrollEmail("")
            setEnrollCourseId("")
            setIsEnrollOpen(false)
            setSelectedStudent(null)
            setSearchQuery("")
            setSearchResults([])
            fetchData() // Refresh list
        } catch (error: any) {
            alert(error.response?.data?.detail || "Enrollment failed")
        } finally {
            setEnrollLoading(false)
        }
    }

    const toggleEnrollment = async (studentId: number, courseId: number, isEnrolled: boolean) => {
        setManageLoading(true)
        try {
            if (isEnrolled) {
                // Remove
                await api.delete(`/courses/${courseId}/students/${studentId}`)
            } else {
                // Add (we need email)
                // Wait, we have the student object, we can use their email.
                const student = students.find(s => s.id === studentId)
                if (!student) return
                await api.post(`/courses/${courseId}/students`, { email: student.email })
            }
            // Refresh local state or refetch
            // Ideally optimistic update, but refetch is safer for sync
            await fetchData()
        } catch (e: any) {
            console.error("Enrollment Action Failed:", e)
            const msg = e.response?.data?.detail || e.message
            alert(typeof msg === 'object' ? JSON.stringify(msg, null, 2) : msg)
        } finally {
            setManageLoading(false)
        }
    }

    const filteredStudents = students.filter(s =>
        s.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        s.email?.toLowerCase().includes(search.toLowerCase())
    )

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5 text-slate-500" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">My Students</h1>
                        <p className="text-slate-500">Manage students and enrollments.</p>
                    </div>
                </div>

                <Dialog open={isEnrollOpen} onOpenChange={setIsEnrollOpen}>
                    <DialogTrigger asChild>
                        <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 flex items-center gap-2">
                            <Plus className="w-4 h-4" />
                            Add Student
                        </button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Enroll New Student</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Find Student</label>
                                {!selectedStudent ? (
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                        <input
                                            className="w-full pl-9 pr-4 py-2 border rounded-md"
                                            placeholder="Search name or email..."
                                            value={searchQuery}
                                            onChange={(e) => {
                                                setSearchQuery(e.target.value)
                                                handleSearch(e.target.value)
                                            }}
                                        />
                                        {searchResults.length > 0 && (
                                            <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-48 overflow-auto">
                                                {searchResults.map(s => (
                                                    <button
                                                        key={s.id}
                                                        onClick={() => {
                                                            setSelectedStudent(s)
                                                            setSearchQuery("")
                                                            setSearchResults([])
                                                            setEnrollEmail(s.email)
                                                        }}
                                                        className="w-full text-left px-4 py-2 hover:bg-slate-50 text-sm"
                                                    >
                                                        <div className="font-medium">{s.full_name}</div>
                                                        <div className="text-xs text-slate-500">{s.email}</div>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-between p-2 border rounded-md bg-slate-50">
                                        <div>
                                            <p className="font-medium text-sm">{selectedStudent.full_name}</p>
                                            <p className="text-xs text-slate-500">{selectedStudent.email}</p>
                                        </div>
                                        <button onClick={() => { setSelectedStudent(null); setEnrollEmail(""); }} className="p-1 hover:bg-slate-200 rounded">
                                            <X className="w-4 h-4 text-slate-500" />
                                        </button>
                                    </div>
                                )}
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Select Course</label>
                                <select
                                    className="w-full p-2 border rounded-md"
                                    value={enrollCourseId}
                                    onChange={e => setEnrollCourseId(e.target.value)}
                                >
                                    <option value="">Select a course...</option>
                                    {courses.map(c => (
                                        <option key={c.id} value={c.id}>{c.title} ({c.code})</option>
                                    ))}
                                </select>
                            </div>
                            <button
                                onClick={handleEnroll}
                                disabled={enrollLoading}
                                className="w-full bg-indigo-600 text-white py-2 rounded-md font-medium hover:bg-indigo-700 disabled:opacity-50"
                            >
                                {enrollLoading ? "Enrolling..." : "Enroll Student"}
                            </button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            placeholder="Search by name or email..."
                            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-200">
                            <tr>
                                <th className="px-6 py-4">Student</th>
                                <th className="px-6 py-4">Enrolled Courses</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr><td colSpan={3} className="px-6 py-12 text-center text-slate-500">Loading...</td></tr>
                            ) : filteredStudents.length === 0 ? (
                                <tr><td colSpan={3} className="px-6 py-12 text-center text-slate-500">No students found.</td></tr>
                            ) : (
                                filteredStudents.map((student) => (
                                    <tr key={student.id} className="hover:bg-slate-50/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600 font-medium">
                                                    {student.full_name?.[0] || <User className="w-4 h-4" />}
                                                </div>
                                                <div>
                                                    <p className="font-medium text-slate-900">{student.full_name}</p>
                                                    <p className="text-slate-500 text-xs">{student.email}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-wrap gap-2">
                                                {student.enrolledCourses?.length > 0 ? (
                                                    student.enrolledCourses.map((c: any) => (
                                                        <span key={c.id} className="inline-flex items-center px-2 py-1 rounded bg-slate-100 text-slate-600 text-xs border border-slate-200">
                                                            <BookOpen className="w-3 h-3 mr-1 opacity-50" />
                                                            {c.code}
                                                        </span>
                                                    ))
                                                ) : (
                                                    <span className="text-slate-400 italic text-xs">No active enrollments</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <Dialog>
                                                <DialogTrigger asChild>
                                                    <button
                                                        onClick={() => setManageStudent(student)}
                                                        className="text-indigo-600 hover:text-indigo-800 font-medium text-xs border border-indigo-200 px-3 py-1 rounded hover:bg-indigo-50 transition-colors"
                                                    >
                                                        Manage
                                                    </button>
                                                </DialogTrigger>
                                                <DialogContent>
                                                    <DialogHeader>
                                                        <DialogTitle>Manage Enrollment: {student.full_name}</DialogTitle>
                                                    </DialogHeader>
                                                    <div className="py-2 space-y-1">
                                                        <p className="text-sm text-slate-500 mb-4">Toggle courses to add or remove this student.</p>
                                                        {courses.map(course => {
                                                            const isEnrolled = student.enrolledCourses?.some((c: any) => c.id === course.id)
                                                            return (
                                                                <div key={course.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50">
                                                                    <div>
                                                                        <p className="font-medium text-sm">{course.title}</p>
                                                                        <p className="text-xs text-slate-500">{course.code}</p>
                                                                    </div>
                                                                    <button
                                                                        onClick={() => toggleEnrollment(student.id, course.id, isEnrolled)}
                                                                        disabled={manageLoading}
                                                                        className={`text-xs px-3 py-1.5 rounded font-medium transition-colors ${isEnrolled
                                                                            ? "bg-red-50 text-red-600 hover:bg-red-100"
                                                                            : "bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                                                                            }`}
                                                                    >
                                                                        {isEnrolled ? "Remove" : "Add"}
                                                                    </button>
                                                                </div>
                                                            )
                                                        })}
                                                    </div>
                                                </DialogContent>
                                            </Dialog>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
