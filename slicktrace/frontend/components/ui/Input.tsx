import * as React from 'react'
import { LucideIcon } from 'lucide-react'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: LucideIcon
  rightIcon?: LucideIcon
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', label, error, hint, leftIcon: LeftIcon, rightIcon: RightIcon, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-medium text-slate-300 select-none">
            {label}
            {props.required && <span className="text-rose-400 ml-1">*</span>}
          </label>
        )}
        <div className="relative flex items-center">
          {LeftIcon && (
            <div className="absolute left-3 pointer-events-none text-slate-400">
              <LeftIcon className="w-3.5 h-3.5" />
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={`w-full bg-slate-950/90 text-slate-100 placeholder-slate-500 text-xs rounded-lg border ${
              error
                ? 'border-rose-500/80 focus:border-rose-400 focus:ring-1 focus:ring-rose-500/50'
                : 'border-slate-700/80 focus:border-sky-400 focus:ring-1 focus:ring-sky-500/50'
            } ${LeftIcon ? 'pl-9' : 'pl-3'} ${RightIcon ? 'pr-9' : 'pr-3'} py-2 transition-all outline-none disabled:opacity-50 disabled:bg-slate-900 ${className}`}
            {...props}
          />
          {RightIcon && (
            <div className="absolute right-3 pointer-events-none text-slate-400">
              <RightIcon className="w-3.5 h-3.5" />
            </div>
          )}
        </div>
        {hint && !error && <p className="text-[11px] text-slate-400">{hint}</p>}
        {error && <p className="text-[11px] font-medium text-rose-400">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
