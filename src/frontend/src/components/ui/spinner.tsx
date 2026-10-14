export function Spinner({
  label = "Loading...",
  className = "",
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center justify-center gap-3 text-sm text-slate-600 ${className}`}
      role="status"
    >
      <span
        aria-hidden
        className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600"
      />
      <span>{label}</span>
    </div>
  );
}
