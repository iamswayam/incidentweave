export function ResultsSkeleton() {
  return (
    <div className="grid gap-4" aria-hidden>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="skeleton mb-3 h-5 w-28 rounded" />
        <div className="skeleton mb-2 h-4 w-full rounded" />
        <div className="skeleton mb-2 h-4 w-5/6 rounded" />
        <div className="skeleton h-4 w-2/3 rounded" />
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="skeleton mb-3 h-5 w-40 rounded" />
        <div className="skeleton mb-2 h-16 w-full rounded" />
        <div className="skeleton h-16 w-full rounded" />
      </div>
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="skeleton mb-3 h-5 w-48 rounded" />
        <div className="grid gap-3 lg:grid-cols-3">
          <div className="skeleton h-40 rounded" />
          <div className="skeleton h-40 rounded" />
          <div className="skeleton h-40 rounded" />
        </div>
      </div>
    </div>
  );
}
