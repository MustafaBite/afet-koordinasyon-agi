// Yeniden kullanılabilir Select (Dropdown) componenti

export default function Select({ 
  label, 
  name, 
  value, 
  onChange, 
  options, 
  error, 
  placeholder = 'Seçiniz...',
  required = false,
  icon 
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
          <span className="absolute inset-y-0 left-3 flex items-center text-slate-400 pointer-events-none z-10">
            <span className="material-symbols-outlined text-xl">{icon}</span>
          </span>
        )}
        <select
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          className={`w-full ${icon ? 'pl-10' : 'pl-4'} pr-10 py-3 rounded-lg bg-slate-100 dark:bg-slate-800 border ${
            error ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'
          } focus:ring-2 focus:ring-primary focus:border-transparent text-sm transition-all appearance-none cursor-pointer`}
        >
          <option value="">{placeholder}</option>
          {Object.entries(options).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        <span className="absolute inset-y-0 right-3 flex items-center text-slate-400 pointer-events-none">
          <span className="material-symbols-outlined text-xl">expand_more</span>
        </span>
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
