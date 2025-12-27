"use client"

import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useRouter, useParams } from "next/navigation"
import * as z from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2, ArrowLeft } from "lucide-react"
import Link from "next/link"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

const courseSchema = z.object({
    title: z.string().min(3, "Title too short"),
    code: z.string().min(2, "Course code is required (e.g. CS101)"),
    description: z.string().optional(),
})

type CourseFormValues = z.infer<typeof courseSchema>

export default function EditCoursePage() {
    const router = useRouter()
    const params = useParams()
    const id = params.id

    const [isLoading, setIsLoading] = useState(false)
    const [isFetching, setIsFetching] = useState(true)

    const {
        register,
        handleSubmit,
        setValue,
        formState: { errors },
    } = useForm<CourseFormValues>({
        resolver: zodResolver(courseSchema),
    })

    useEffect(() => {
        const fetchCourse = async () => {
            try {
                const res = await api.get(`/courses/${id}`)
                const course = res.data
                setValue("title", course.title)
                setValue("code", course.code)
                setValue("description", course.description || "")
            } catch (error) {
                console.error("Failed to fetch course details")
                alert("Failed to load course details")
                router.push("/dashboard/teacher/courses")
            } finally {
                setIsFetching(false)
            }
        }

        if (id) {
            fetchCourse()
        }
    }, [id, setValue, router])

    async function onSubmit(data: CourseFormValues) {
        setIsLoading(true)
        try {
            await api.put(`/courses/${id}`, data)
            router.push("/dashboard/teacher/courses")
        } catch (error) {
            console.error(error)
            alert("Failed to update course")
        } finally {
            setIsLoading(false)
        }
    }

    if (isFetching) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
            </div>
        )
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link href="/dashboard/teacher/courses" className="p-2 hover:bg-slate-100 rounded-full transition-colors">
                    <ArrowLeft className="w-5 h-5 text-slate-500" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Edit Course</h1>
                    <p className="text-slate-500">Update course details.</p>
                </div>
            </div>

            <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Course Title</label>
                        <input
                            {...register("title")}
                            className={cn(
                                "flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 border-input bg-transparent",
                                errors.title && "border-red-500"
                            )}
                            placeholder="Introduction to Artificial Intelligence"
                        />
                        {errors.title && <p className="text-xs text-red-500">{errors.title.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Course Code</label>
                        <input
                            {...register("code")}
                            className={cn(
                                "flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 border-input bg-transparent",
                                errors.code && "border-red-500"
                            )}
                            placeholder="AI-101"
                        />
                        {errors.code && <p className="text-xs text-red-500">{errors.code.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium">Description</label>
                        <textarea
                            {...register("description")}
                            className="flex min-h-[100px] w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-slate-900 border-input bg-transparent resize-y"
                            placeholder="Brief summary of what this course covers..."
                        />
                    </div>

                    <div className="flex justify-end pt-4">
                        <button
                            disabled={isLoading}
                            className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-800 h-10 px-8 py-2"
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Update Course
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
