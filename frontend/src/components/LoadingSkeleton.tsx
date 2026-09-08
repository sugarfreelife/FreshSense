export default function LoadingSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div aria-busy="true" aria-label="Loading" className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-16 animate-pulse rounded-xl bg-slate-200"
        />
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  );
}
