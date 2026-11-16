import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) return "—";
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(ms >= 10_000 ? 0 : 1)} s`;
}

export function formatScore(value: number | null | undefined, digits = 3): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function relativeScore(
  value: number | null | undefined,
  max: number | null | undefined,
): number {
  if (value == null || max == null || max <= 0) return 0;
  return Math.max(0, Math.min(1, value / max));
}

export function truncate(text: string, max = 120): string {
  const trimmed = text.trim();
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max - 1)}…`;
}
