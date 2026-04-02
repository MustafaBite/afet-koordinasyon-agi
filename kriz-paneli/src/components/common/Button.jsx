// Yeniden kullanılabilir Button componenti

export default function Button({ 
  children, 
  type = 'button', 
  onClick, 
  variant = 'primary', 
  disabled = false,
  loading = false,
  fullWidth = false,
  icon
}) {
  const baseClasses = 'px-6 py-3 rounded-lg font-semibold text-sm transition-all flex items-center justify-center gap-2';
  
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary/90 disabled:bg-slate-300 disabled:cursor-not-allowed',
    secondary: 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600',
    danger: 'bg-red-500 text-white hover:bg-red-600 disabled:bg-red-300',
    ghost: 'bg-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseClasses} ${variants[variant]} ${fullWidth ? 'w-full' : ''}`}
    >
      {loading ? (
        <>
          <span className="material-symbols-outlined animate-spin">progress_activity</span>
          Yükleniyor...
        </>
      ) : (
        <>
          {icon && <span className="material-symbols-outlined">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
}
