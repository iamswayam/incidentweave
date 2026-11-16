import { Loader2 } from "lucide-react";
import type { KeyboardEvent } from "react";
import type { RepositorySummary } from "@/api/types";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const MAX_QUERY_CHARS = 2000;
const MAX_LIMIT = 20;

interface QueryPanelProps {
  repositories: RepositorySummary[];
  repositoryName: string;
  query: string;
  limit: number;
  busy: boolean;
  onRepositoryChange: (name: string) => void;
  onQueryChange: (value: string) => void;
  onLimitChange: (limit: number) => void;
  onSubmit: () => void;
}

export function QueryPanel({
  repositories,
  repositoryName,
  query,
  limit,
  busy,
  onRepositoryChange,
  onQueryChange,
  onLimitChange,
  onSubmit,
}: QueryPanelProps) {
  const length = query.length;
  const canSubmit =
    !busy &&
    repositoryName.length > 0 &&
    query.trim().length > 0 &&
    length <= MAX_QUERY_CHARS;

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      if (canSubmit) onSubmit();
    }
  }

  return (
    <section className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
            Investigation
          </p>
          <h2 className="text-lg font-semibold tracking-tight">Ask a question</h2>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            Limit
            <Select
              value={String(limit)}
              onValueChange={(value) => onLimitChange(Number(value))}
              disabled={busy}
            >
              <SelectTrigger className="h-8 w-[4.5rem]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: MAX_LIMIT }, (_, index) => index + 1).map((value) => (
                  <SelectItem key={value} value={String(value)}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        </div>
      </div>

      <div className="mb-3 grid gap-2">
        <label className="text-xs text-muted-foreground">Repository</label>
        <Select
          value={repositoryName || undefined}
          onValueChange={onRepositoryChange}
          disabled={busy || repositories.length === 0}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select a repository" />
          </SelectTrigger>
          <SelectContent>
            {repositories.map((repo) => (
              <SelectItem key={repo.name} value={repo.name}>
                <span className="font-mono text-xs">{repo.name}</span>
                <span className="ml-2 text-muted-foreground">
                  {repo.embedded_chunk_count}/{repo.chunk_count} embedded
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-2">
        <Textarea
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What failed in the ingestion pipeline?"
          disabled={busy}
          maxLength={MAX_QUERY_CHARS + 200}
        />
        <div className="flex items-center justify-between gap-3">
          <p
            className={cn(
              "font-mono text-xs tabular-nums text-muted-foreground",
              length >= 1800 && length <= MAX_QUERY_CHARS && "text-warning",
              length > MAX_QUERY_CHARS && "text-destructive",
            )}
          >
            {length}/{MAX_QUERY_CHARS}
          </p>
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              ⌘/Ctrl+Enter
            </span>
            <Button type="button" onClick={onSubmit} disabled={!canSubmit}>
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {busy ? "Investigating…" : "Investigate"}
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
