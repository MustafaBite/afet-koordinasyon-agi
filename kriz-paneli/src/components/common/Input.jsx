// Yeniden kullanılabilir Input componenti

export default function Input({ 
  label, 
  type = 'text', 
  name, 
  value, 
  onChange, 
  error, 
  placeholder,
  required = false,
  icon,
  autoComplete
}) {
  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={name} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}
      <div className="relative">
        {icon && (
          <span className="absolute inset-y-0 left-3 flex items-center text-slate-400">
            <span className="material-symbols-outlined text-xl">{icon}</span>
          </span>
        )}
        <input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={`w-full ${icon ? 'pl-10' : 'pl-4'} pr-4 py-3 rounded-lg bg-slate-100 dark:bg-slate-800 border ${
            error ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'
          } focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all`}
        />
      </div>
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1">
          <span className="material-symbols-outlined text-sm">error</span>
          {error}
        </p>
      )}
    </div>
  );
}
