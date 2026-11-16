import { useMemo } from "react";
import type { EvidenceSource, InvestigationEvidence } from "@/api/types";
import { ScoreBar } from "@/components/ScoreBar";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatLineRange } from "@/lib/github";
import { cn, formatScore } from "@/lib/utils";

interface RetrievalBreakdownProps {
  evidence: InvestigationEvidence[];
  citedChunkIds: string[];
}

function sourceBadge(source: EvidenceSource | null): "default" | "secondary" | "outline" {
  if (source === "both") return "default";
  if (source === "vector") return "outline";
  return "secondary";
}

export function RetrievalBreakdown({ evidence, citedChunkIds }: RetrievalBreakdownProps) {
  const cited = useMemo(() => new Set(citedChunkIds.map(String)), [citedChunkIds]);

  const semantic = useMemo(
    () =>
      evidence
        .filter((item) => item.source === "vector" || item.source === "both")
        .slice()
        .sort((a, b) => (b.vector_score ?? -1) - (a.vector_score ?? -1)),
    [evidence],
  );

  const fulltext = useMemo(
    () =>
      evidence
        .filter((item) => item.source === "fulltext" || item.source === "both")
        .slice()
        .sort((a, b) => (b.fts_score ?? -1) - (a.fts_score ?? -1)),
    [evidence],
  );

  const fused = useMemo(
    () =>
      evidence
        .slice()
        .sort((a, b) => (b.rrf_score ?? -1) - (a.rrf_score ?? -1)),
    [evidence],
  );

  const maxVector = Math.max(0, ...semantic.map((item) => item.vector_score ?? 0));
  const maxFts = Math.max(0, ...fulltext.map((item) => item.fts_score ?? 0));
  const maxRrf = Math.max(0, ...fused.map((item) => item.rrf_score ?? 0));

  if (!evidence.length) {
    return (
      <section className="animate-fade-in rounded-lg border border-border bg-card p-4">
        <h2 className="text-sm font-semibold tracking-tight">Retrieval breakdown</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          No debug evidence was returned. Confirm the request sent <code>debug: true</code>.
        </p>
      </section>
    );
  }

  return (
    <section className="animate-fade-in rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold tracking-tight">Retrieval breakdown</h2>
        <p className="text-xs text-muted-foreground">
          Cited chunks are highlighted in RRF — the key evaluation signal.
        </p>
      </div>

      <div className="hidden gap-3 lg:grid lg:grid-cols-3">
        <EvidenceColumn
          title="Semantic search"
          empty="No vector hits."
          items={semantic}
          scoreKey="vector_score"
          maxScore={maxVector}
          cited={cited}
          showCitedBadge={false}
        />
        <EvidenceColumn
          title="Fulltext search"
          empty="No fulltext hits."
          items={fulltext}
          scoreKey="fts_score"
          maxScore={maxFts}
          cited={cited}
          showCitedBadge={false}
        />
        <EvidenceColumn
          title="RRF fusion"
          empty="No fused results."
          items={fused}
          scoreKey="rrf_score"
          maxScore={maxRrf}
          cited={cited}
          showCitedBadge
          showSource
        />
      </div>

      <div className="lg:hidden">
        <Tabs defaultValue="rrf">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="semantic">Semantic</TabsTrigger>
            <TabsTrigger value="fulltext">Fulltext</TabsTrigger>
            <TabsTrigger value="rrf">RRF</TabsTrigger>
          </TabsList>
          <TabsContent value="semantic">
            <EvidenceColumn
              title="Semantic search"
              empty="No vector hits."
              items={semantic}
              scoreKey="vector_score"
              maxScore={maxVector}
              cited={cited}
              showCitedBadge={false}
              compact
            />
          </TabsContent>
          <TabsContent value="fulltext">
            <EvidenceColumn
              title="Fulltext search"
              empty="No fulltext hits."
              items={fulltext}
              scoreKey="fts_score"
              maxScore={maxFts}
              cited={cited}
              showCitedBadge={false}
              compact
            />
          </TabsContent>
          <TabsContent value="rrf">
            <EvidenceColumn
              title="RRF fusion"
              empty="No fused results."
              items={fused}
              scoreKey="rrf_score"
              maxScore={maxRrf}
              cited={cited}
              showCitedBadge
              showSource
              compact
            />
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}

function EvidenceColumn({
  title,
  empty,
  items,
  scoreKey,
  maxScore,
  cited,
  showCitedBadge,
  showSource = false,
  compact = false,
}: {
  title: string;
  empty: string;
  items: InvestigationEvidence[];
  scoreKey: "vector_score" | "fts_score" | "rrf_score";
  maxScore: number;
  cited: Set<string>;
  showCitedBadge: boolean;
  showSource?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={cn(!compact && "rounded-md border border-border bg-background/30 p-3")}>
      {!compact ? (
        <h3 className="mb-2 text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
          {title}
        </h3>
      ) : null}
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{empty}</p>
      ) : (
        <ul className="grid gap-2">
          {items.map((item, index) => {
            const isCited = cited.has(String(item.chunk_id));
            const score = item[scoreKey];
            return (
              <li
                key={`${scoreKey}-${item.chunk_id}-${index}`}
                className={cn(
                  "rounded-md border px-2.5 py-2 transition-colors",
                  showCitedBadge && isCited
                    ? "border-primary/40 bg-cited"
                    : "border-border/80 bg-card",
                )}
              >
                <div className="mb-1 flex flex-wrap items-center gap-1.5">
                  <span className="font-mono text-[11px] text-muted-foreground">
                    #{index + 1}
                  </span>
                  {showSource && item.source ? (
                    <Badge variant={sourceBadge(item.source)}>{item.source}</Badge>
                  ) : null}
                  {showCitedBadge && isCited ? <Badge variant="cited">cited</Badge> : null}
                </div>
                <p className="truncate font-mono text-xs" title={item.file_path}>
                  {item.file_path || "unknown path"}
                </p>
                <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                  {formatLineRange(item.start_line, item.end_line)}
                </p>
                <ScoreBar
                  className="mt-2"
                  value={score}
                  max={maxScore}
                  label={formatScore(score)}
                />
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
