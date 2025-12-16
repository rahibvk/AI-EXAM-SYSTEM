"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Loader2, GraduationCap } from "lucide-react"
import api from "@/lib/api"
import { cn } from "@/lib/utils"

const loginSchema = z.object({
    username: z.string().email("Invalid email address"),
    password: z.string().min(1, "Password is required"),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    })

    async function onSubmit(data: LoginFormValues) {
        setIsLoading(true)
        setError("")

        // FormData for OAuth2PasswordRequestForm
        const formData = new FormData()
        formData.append("username", data.username)
        formData.append("password", data.password)

        try {
            const res = await api.post("/login", formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            localStorage.setItem("token", res.data.access_token)
            // Determine role redirect later, for now go to dashboard
            // Fetch user to redirect
            const userRes = await api.get("/me", {
                headers: { Authorization: `Bearer ${res.data.access_token}` }
            })
            const role = userRes.data.role
            if (role === 'teacher' || role === 'admin') {
                router.push("/dashboard/teacher")
            } else {
                router.push("/dashboard/student")
            }
        } catch (err: any) {
            console.error("Login error", err)
            const detail = err.response?.data?.detail
            if (typeof detail === 'string') {
                setError(detail)
            } else if (err.response?.data) {
                setError(JSON.stringify(err.response.data))
            } else {
                setError(err.message || "Something went wrong")
            }
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen grid lg:grid-cols-2">
            {/* Left Side - Hero */}
            <div className="hidden lg:flex flex-col bg-slate-900 text-white p-10 justify-between">
                <div className="flex items-center gap-2">
                    <GraduationCap className="w-8 h-8 text-blue-400" />
                    <span className="font-bold text-xl tracking-tight">AI Exam System</span>
                </div>
                <div className="max-w-md">
                    <h1 className="text-4xl font-bold mb-4">Intelligent Assessment for Modern Education</h1>
                    <p className="text-slate-400 text-lg">
                        Experience seamless exam creation, AI-powered grading, and instant feedback.
                    </p>
                </div>
                <cite className="text-slate-500 text-sm">© 2024 Exam AI Inc.</cite>
            </div>

            {/* Right Side - Form */}
            <div className="flex items-center justify-center p-8 bg-slate-50">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-sm space-y-6 bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-slate-900"
                >
                    <div className="space-y-2 text-center">
                        <h2 className="text-2xl font-bold tracking-tight">Welcome Back</h2>
                        <p className="text-sm text-slate-500">Enter your credentials to access your account</p>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70" htmlFor="email">Email</label>
                            <input
                                {...register("username")}
                                className={cn(
                                    "flex h-10 w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                                    errors.username && "border-red-500 focus:ring-red-500"
                                )}
                                placeholder="name@example.com"
                            />
                            {errors.username && <p className="text-xs text-red-500">{errors.username.message}</p>}
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70" htmlFor="password">Password</label>
                            <input
                                {...register("password")}
                                type="password"
                                className={cn(
                                    "flex h-10 w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                                    errors.password && "border-red-500 focus:ring-red-500"
                                )}
                            />
                            {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
                        </div>

                        {error && <div className="p-3 text-sm text-red-500 bg-red-50 rounded-md">{error}</div>}

                        <button
                            disabled={isLoading}
                            className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-slate-900 text-white hover:bg-slate-900/90 h-10 px-4 py-2 w-full"
                        >
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Sign In
                        </button>
                    </form>

                    <div className="text-center text-sm text-slate-500">
                        Don't have an account? <Link href="/register" className="underline underline-offset-4 hover:text-slate-900">Sign up</Link>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
