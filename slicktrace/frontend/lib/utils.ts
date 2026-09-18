/**
 * SlickTrace v2 — Utility functions
 */
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatScore(score?: number | null): string {
  if (score == null) return 'N/A'
  return score.toFixed(1)
}

export function truncateHash(hash: string, chars = 16): string {
  if (hash.length <= chars * 2 + 3) return hash
  return `${hash.slice(0, chars)}…${hash.slice(-8)}`
}
