import * as React from 'react'
import { LucideIcon, Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline' | 'accent'
  size?: 'sm' | 'md' | 'lg' | 'icon'
  isLoading?: boolean
  leftIcon?: LucideIcon
  rightIcon?: LucideIcon
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = '',
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon: LeftIcon,
      rightIcon: RightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-all duration-150 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500/50 disabled:opacity-50 disabled:cursor-not-allowed select-none'

    const sizeStyles = {
      sm: 'text-xs px-2.5 py-1.5 gap-1.5',
      md: 'text-xs px-3.5 py-2 gap-2',
      lg: 'text-sm px-4 py-2.5 gap-2.5',
      icon: 'p-2 aspect-square',
    }

    const variantStyles = {
      primary:
        'bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-950/50 border border-sky-400/30 active:scale-[0.98]',
      secondary:
        'bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 hover:border-slate-600 shadow-sm active:scale-[0.98]',
      accent:
        'bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-lg shadow-cyan-950/50 border border-cyan-300/40 active:scale-[0.98]',
      danger:
        'bg-rose-600/90 hover:bg-rose-600 text-white border border-rose-500/40 shadow-lg shadow-rose-950/50 active:scale-[0.98]',
      ghost:
        'bg-transparent hover:bg-slate-800/60 text-slate-300 hover:text-white border border-transparent',
      outline:
        'bg-transparent hover:bg-sky-500/10 text-sky-400 border border-sky-500/40 hover:border-sky-400',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          LeftIcon && <LeftIcon className="w-3.5 h-3.5 shrink-0" />
        )}
        {children}
        {!isLoading && RightIcon && <RightIcon className="w-3.5 h-3.5 shrink-0" />}
      </button>
    )
  }
)

Button.displayName = 'Button'
