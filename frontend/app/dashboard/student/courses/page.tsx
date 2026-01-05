"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { BookOpen, User, Loader2 } from "lucide-react"
import api from "@/lib/api"
import { useRouter } from "next/navigation"

interface Course {
    id: number
    title: string
    code: string
    description: string
    teacher_id: number
}

/**
 * Student Courses Page
 * 
 * Displays a catalog of all available courses for the student.
 * - Lists courses with Title, Code, and Description.
 * - Allows navigation to specific course pages for enrollment or exam viewing.
 */
export default function StudentCoursesPage() {
    const [courses, setCourses] = useState<Course[]>([])
    const [loading, setLoading] = useState(true)
    const router = useRouter()

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                // Fetch all available courses for browsing
                const res = await api.get("/courses/")
                setCourses(res.data)
            } catch (error) {
                console.error("Failed to fetch courses")
            } finally {
                setLoading(false)
            }
        }
        fetchCourses()
    }, [])

    if (loading) {
        return <div className="flex h-[50vh] items-center justify-center"><Loader2 className="animate-spin text-slate-400" /></div>
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Browse Courses</h1>
                <p className="text-slate-500">Find courses and take exams.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {courses.map((course, i) => (
                    <motion.div
                        key={course.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="group bg-white border border-slate-200 rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => router.push(`/dashboard/student/courses/${course.id}`)}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                <BookOpen className="w-6 h-6" />
                            </div>
                        </div>

                        <h3 className="text-lg font-semibold mb-1">{course.title}</h3>
                        <p className="text-sm text-slate-500 mb-4 font-mono">{course.code}</p>

                        <p className="text-sm text-slate-600 line-clamp-2">{course.description || "No description provided."}</p>

                        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center text-xs text-slate-500 gap-2">
                            <User className="w-3 h-3" />
                            <span>Teacher ID: {course.teacher_id}</span>
                        </div>
                    </motion.div>
                ))}

                {courses.length === 0 && (
                    <div className="col-span-full py-12 text-center">
                        <p className="text-slate-500">No available courses found.</p>
                    </div>
                )}
            </div>
        </div>
    )
}
