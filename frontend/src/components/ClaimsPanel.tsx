import { ChevronDown, ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";
import type { InvestigationClaim, InvestigationEvidence } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { buildGithubUrl, formatLineRange } from "@/lib/github";
import { cn } from "@/lib/utils";

interface ClaimsPanelProps {
  claims: InvestigationClaim[];
  evidence: InvestigationEvidence[];
  githubBaseUrl?: string;
}

function claimText(claim: InvestigationClaim): string {
  return (claim.text || claim.claim || "").trim() || "Untitled claim";
}

function claimCitations(claim: InvestigationClaim) {
  return claim.citations || claim.evidence || [];
}

export function ClaimsPanel({ claims, evidence, githubBaseUrl }: ClaimsPanelProps) {
  const evidenceById = useMemo(() => {
    const map = new Map<string, InvestigationEvidence>();
    for (const item of evidence) map.set(item.chunk_id, item);
    return map;
  }, [evidence]);

  if (!claims.length) {
    return (
      <section className="animate-fade-in rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-semibold tracking-tight">Claims & citations</h2>
        <p className="mt-2 text-sm text-muted-foreground">No claims returned for this investigation.</p>
      </section>
    );
  }

  return (
    <section className="animate-fade-in rounded-lg border border-border bg-card p-4">
      <h2 className="mb-3 text-sm font-semibold tracking-tight">Claims & citations</h2>
      <div className="grid gap-2">
        {claims.map((claim, index) => (
          <ClaimCard
            key={`${claimText(claim)}-${index}`}
            claim={claim}
            evidenceById={evidenceById}
            githubBaseUrl={githubBaseUrl}
          />
        ))}
      </div>
    </section>
  );
}

function ClaimCard({
  claim,
  evidenceById,
  githubBaseUrl,
}: {
  claim: InvestigationClaim;
  evidenceById: Map<string, InvestigationEvidence>;
  githubBaseUrl?: string;
}) {
  const [open, setOpen] = useState(true);
  const citations = claimCitations(claim);
  const supported = claim.supported ?? citations.length > 0;

  return (
    <article className="rounded-md border border-border bg-background/40 p-3">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm leading-relaxed">{claimText(claim)}</p>
        <Badge variant={supported ? "success" : "destructive"}>
          {supported ? "supported" : "unsupported"}
        </Badge>
      </div>

      <button
        type="button"
        className="mt-2 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        onClick={() => setOpen((value) => !value)}
      >
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
        {citations.length} citation{citations.length === 1 ? "" : "s"}
      </button>

      {open ? (
        <ul className="mt-2 grid gap-1.5">
          {citations.length === 0 ? (
            <li className="text-xs text-muted-foreground">No citations attached.</li>
          ) : (
            citations.map((citation, index) => {
              const meta = evidenceById.get(citation.chunk_id);
              const filePath = citation.file_path || meta?.file_path || "unknown path";
              const start = citation.start_line ?? meta?.start_line ?? null;
              const end = citation.end_line ?? meta?.end_line ?? null;
              const href = buildGithubUrl(githubBaseUrl, filePath, start, end);

              return (
                <li
                  key={`${citation.chunk_id}-${index}`}
                  className="rounded border border-border/70 bg-card px-2.5 py-2"
                >
                  <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
                    {href ? (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                      >
                        {filePath}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      <span>{filePath}</span>
                    )}
                    <span className="text-muted-foreground">{formatLineRange(start, end)}</span>
                    <span className="text-muted-foreground">{citation.chunk_id}</span>
                  </div>
                  {citation.quote ? (
                    <p className="mt-1 text-xs italic text-muted-foreground">
                      “{citation.quote}”
                    </p>
                  ) : null}
                </li>
              );
            })
          )}
        </ul>
      ) : null}
    </article>
  );
}
