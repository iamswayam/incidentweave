import { AlertTriangle } from "lucide-react";
import type { InvestigationResponse } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { formatLatency } from "@/lib/utils";

interface AnswerPanelProps {
  result: InvestigationResponse;
}

function outcomeVariant(
  outcome: string,
  unavailable: boolean,
  degraded: boolean,
): "success" | "warning" | "destructive" | "secondary" {
  if (unavailable || outcome.includes("unavailable") || outcome === "insufficient_evidence") {
    return "warning";
  }
  if (degraded) return "warning";
  if (outcome === "answered") return "success";
  return "secondary";
}

function ratingLabel(rating: string): string {
  const value = rating.trim().toLowerCase();
  if (!value || value === "not_applicable") return "n/a";
  if (/^\d+(\.\d+)?$/.test(value)) return `${value}/10`;
  return value;
}

export function AnswerPanel({ result }: AnswerPanelProps) {
  const unavailable = result.unavailable_answer || result.outcome === "insufficient_evidence";
  const mutedDiagnosis = unavailable || !result.diagnosis.trim();

  return (
    <section className="animate-fade-in rounded-lg border border-border bg-card p-4">
      {result.degraded ? (
        <div className="mb-3 flex items-start gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div>
            <p className="font-medium">Degraded response</p>
            <p className="text-xs opacity-90">
              {result.degraded_reason
                ? `Reason: ${result.degraded_reason}`
                : "The pipeline returned a degraded outcome."}
            </p>
          </div>
        </div>
      ) : null}

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Badge variant={outcomeVariant(result.outcome, unavailable, result.degraded)}>
          {result.outcome}
        </Badge>
        <Badge variant="outline">{ratingLabel(result.model_self_rating)}</Badge>
        {result.model ? (
          <span className="font-mono text-xs text-muted-foreground">{result.model}</span>
        ) : null}
      </div>

      <h2 className="mb-2 text-sm font-medium text-muted-foreground">Diagnosis</h2>
      <p
        className={
          mutedDiagnosis
            ? "text-base italic leading-relaxed text-muted-foreground"
            : "text-base leading-relaxed text-foreground"
        }
      >
        {result.diagnosis?.trim() || "No diagnosis returned."}
      </p>

      {result.uncertainty_note?.trim() ? (
        <p className="mt-3 rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          {result.uncertainty_note}
        </p>
      ) : null}

      <div className="mt-4 flex justify-end">
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          {formatLatency(result.latency_ms)}
        </span>
      </div>
    </section>
  );
}
