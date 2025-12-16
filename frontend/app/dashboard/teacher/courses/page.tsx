"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { Plus, BookOpen, MoreVertical, Loader2 } from "lucide-react"
import api from "@/lib/api"
import { useRouter } from "next/navigation"

interface Course {
    id: number
    title: string
    code: string
    description: string
    materials: any[]
}

export default function CoursesPage() {
    const [courses, setCourses] = useState<Course[]>([])
    const [loading, setLoading] = useState(true)
    const router = useRouter()

    useEffect(() => {
        const fetchCourses = async () => {
            try {
                const res = await api.get("/courses/my-courses")
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
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">My Courses</h1>
                    <p className="text-slate-500">Manage your subjects and study materials.</p>
                </div>
                <Link
                    href="/dashboard/teacher/courses/new"
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 h-10 px-4 py-2 gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Create Course
                </Link>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {courses.map((course, i) => (
                    <motion.div
                        key={course.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                        className="group relative bg-white border border-slate-200 rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => router.push(`/dashboard/teacher/courses/${course.id}`)}
                    >
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                                <BookOpen className="w-6 h-6" />
                            </div>
                            <button className="p-1 hover:bg-slate-100 rounded text-slate-400">
                                <MoreVertical className="w-4 h-4" />
                            </button>
                        </div>

                        <h3 className="text-lg font-semibold mb-1">{course.title}</h3>
                        <p className="text-sm text-slate-500 mb-4 font-mono">{course.code}</p>

                        <p className="text-sm text-slate-600 line-clamp-2">{course.description || "No description provided."}</p>

                        <div className="mt-6 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-500">
                            <span>{course.materials?.length || 0} Materials</span>
                            <span>Active</span>
                        </div>
                    </motion.div>
                ))}

                {courses.length === 0 && (
                    <div className="col-span-full py-12 text-center border-2 border-dashed border-slate-200 rounded-xl">
                        <div className="bg-slate-50 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <BookOpen className="w-6 h-6 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900">No courses yet</h3>
                        <p className="text-slate-500 text-sm mt-1 mb-4">Create your first course to get started.</p>
                        <Link
                            href="/dashboard/teacher/courses/new"
                            className="inline-flex items-center text-sm font-medium text-blue-600 hover:underline"
                        >
                            Create Course &rarr;
                        </Link>
                    </div>
                )}
            </div>
        </div>
    )
}
