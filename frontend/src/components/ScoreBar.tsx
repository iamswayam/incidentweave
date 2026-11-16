import { cn, formatScore, relativeScore } from "@/lib/utils";

interface ScoreBarProps {
  value: number | null | undefined;
  max: number | null | undefined;
  label?: string;
  className?: string;
}

export function ScoreBar({ value, max, label, className }: ScoreBarProps) {
  const ratio = relativeScore(value, max);

  return (
    <div className={cn("flex min-w-0 items-center gap-2", className)}>
      <div className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary/80 transition-[width] duration-300"
          style={{ width: `${ratio * 100}%` }}
        />
      </div>
      <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">
        {label ?? formatScore(value)}
      </span>
    </div>
  );
}
