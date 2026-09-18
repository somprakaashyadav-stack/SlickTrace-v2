import * as React from 'react'
import { ChevronDown } from 'lucide-react'

export interface DropdownOption {
  value: string
  label: string
}

export interface DropdownProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  options: DropdownOption[]
  error?: string
}

export const Dropdown = React.forwardRef<HTMLSelectElement, DropdownProps>(
  ({ className = '', label, options, error, id, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-medium text-slate-300">
            {label}
            {props.required && <span className="text-rose-400 ml-1">*</span>}
          </label>
        )}
        <div className="relative flex items-center">
          <select
            id={selectId}
            ref={ref}
            className={`w-full appearance-none bg-slate-950/90 text-slate-100 text-xs rounded-lg border ${
              error ? 'border-rose-500' : 'border-slate-700/80 focus:border-sky-400'
            } px-3 py-2 pr-8 transition-all outline-none focus:ring-1 focus:ring-sky-500/50 ${className}`}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-slate-900 text-slate-100">
                {opt.label}
              </option>
            ))}
          </select>
          <div className="absolute right-3 pointer-events-none text-slate-400">
            <ChevronDown className="w-3.5 h-3.5" />
          </div>
        </div>
        {error && <p className="text-[11px] font-medium text-rose-400">{error}</p>}
      </div>
    )
  }
)

Dropdown.displayName = 'Dropdown'
