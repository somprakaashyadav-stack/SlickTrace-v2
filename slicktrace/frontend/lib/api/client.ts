/**
 * SlickTrace v2 — API Client
 * Thin wrapper around axios for typed API calls.
 */
import axios from 'axios'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export const api = {
  async get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    const { data } = await axiosInstance.get<T>(path, { params })
    return data
  },

  async post<T>(path: string, body?: unknown): Promise<T> {
    const { data } = await axiosInstance.post<T>(path, body)
    return data
  },

  async postForm<T>(path: string, formData: FormData): Promise<T> {
    const { data } = await axiosInstance.post<T>(path, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  async patch<T>(path: string, body?: unknown): Promise<T> {
    const { data } = await axiosInstance.patch<T>(path, body)
    return data
  },

  async delete(path: string): Promise<void> {
    await axiosInstance.delete(path)
  },
}

export default axiosInstance
