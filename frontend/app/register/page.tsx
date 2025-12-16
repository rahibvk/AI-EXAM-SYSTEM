"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Loader2, Eye, EyeOff } from "lucide-react" // Added icons
import api from "@/lib/api"
import { cn } from "@/lib/utils"

const registerSchema = z.object({
    full_name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Invalid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
    role: z.enum(["student", "teacher"]),
}).refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
})

type RegisterFormValues = z.infer<typeof registerSchema>

export default function RegisterPage() {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")

    // Password Visibility States
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
        defaultValues: { role: "student" }
    })

    async function onSubmit(data: RegisterFormValues) {
        setIsLoading(true)
        setError("")

        try {
            const payload = {
                full_name: data.full_name,
                email: data.email,
                password: data.password,
                role: data.role
            }
            // Log for debugging
            console.log("Submitting payload:", payload)
            const res = await api.post("/register", payload)
            console.log("Response:", res)
            router.push("/login")
        } catch (err: any) {
            console.error("Registration Error:", err)
            const errorMsg = err.response?.data?.detail
                || err.message
                || "Connection failed. Is the backend running?"
            setError(errorMsg)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md space-y-6 bg-white p-8 rounded-2xl shadow-sm border border-slate-100 text-slate-900"
            >
                <div className="space-y-2 text-center">
                    <h2 className="text-2xl font-bold tracking-tight text-slate-900">Create an Account</h2>
                    <p className="text-sm text-slate-500">Join the AI-powered learning platform</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900" htmlFor="full_name">Full Name</label>
                        <input
                            {...register("full_name")}
                            className={cn("flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:ring-2 focus:ring-slate-900 border-input bg-transparent", errors.full_name && "border-red-500")}
                        />
                        {errors.full_name && <p className="text-xs text-red-500">{errors.full_name.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900" htmlFor="email">Email</label>
                        <input
                            {...register("email")}
                            className={cn("flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:ring-2 focus:ring-slate-900 border-input bg-transparent", errors.email && "border-red-500")}
                        />
                        {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900" htmlFor="role">I am a</label>
                        <select
                            {...register("role")}
                            className="flex h-10 w-full rounded-md border border-slate-200 bg-transparent px-3 py-2 text-sm text-slate-900 focus:ring-2 focus:ring-slate-900"
                        >
                            <option value="student">Student</option>
                            <option value="teacher">Teacher</option>
                        </select>
                    </div>

                    {/* Password Field */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900" htmlFor="password">Password</label>
                        <div className="relative">
                            <input
                                {...register("password")}
                                type={showPassword ? "text" : "password"}
                                className={cn("flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:ring-2 focus:ring-slate-900 border-input bg-transparent pr-10", errors.password && "border-red-500")}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                            >
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                        {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
                    </div>

                    {/* Confirm Password Field */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-900" htmlFor="confirmPassword">Confirm Password</label>
                        <div className="relative">
                            <input
                                {...register("confirmPassword")}
                                type={showConfirmPassword ? "text" : "password"}
                                className={cn("flex h-10 w-full rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:ring-2 focus:ring-slate-900 border-input bg-transparent pr-10", errors.confirmPassword && "border-red-500")}
                            />
                            <button
                                type="button"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                            >
                                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                        {errors.confirmPassword && <p className="text-xs text-red-500">{errors.confirmPassword.message}</p>}
                    </div>

                    {error && <div className="p-3 text-sm text-red-500 bg-red-50 rounded-md border border-red-200">{error}</div>}

                    <button
                        disabled={isLoading}
                        className="w-full inline-flex items-center justify-center rounded-md text-sm font-medium bg-slate-900 text-white hover:bg-slate-900/90 h-10 px-4 py-2"
                    >
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Create Account
                    </button>
                </form>

                <div className="text-center text-sm text-slate-500">
                    Already have an account? <Link href="/login" className="underline underline-offset-4 hover:text-slate-900">Sign in</Link>
                </div>
            </motion.div>
        </div>
    )
}
