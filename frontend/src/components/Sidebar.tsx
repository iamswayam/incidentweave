import {
  ChevronsLeft,
  ChevronsRight,
  Moon,
  RefreshCw,
  Settings2,
  Sun,
} from "lucide-react";
import type { InvestigationSummary, RepositorySummary } from "@/api/types";
import type { Theme } from "@/hooks/useTheme";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, formatLatency, truncate } from "@/lib/utils";

interface SidebarProps {
  collapsed: boolean;
  theme: Theme;
  healthy: boolean | null;
  repositories: RepositorySummary[];
  repositoryName: string;
  history: InvestigationSummary[];
  activeId: number | null;
  historyLoading: boolean;
  hasMoreHistory: boolean;
  onToggleCollapsed: () => void;
  onToggleTheme: () => void;
  onOpenSettings: () => void;
  onRefreshRepositories: () => void;
  onSelectRepository: (name: string) => void;
  onSelectInvestigation: (id: number) => void;
  onLoadMoreHistory: () => void;
}

export function Sidebar({
  collapsed,
  theme,
  healthy,
  repositories,
  repositoryName,
  history,
  activeId,
  historyLoading,
  hasMoreHistory,
  onToggleCollapsed,
  onToggleTheme,
  onOpenSettings,
  onRefreshRepositories,
  onSelectRepository,
  onSelectInvestigation,
  onLoadMoreHistory,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r border-border bg-sidebar text-sidebar-foreground transition-[width] duration-200",
        collapsed ? "w-[4.25rem]" : "w-[18.5rem]",
      )}
    >
      <div className="flex items-center gap-2 border-b border-border px-3 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/15 font-mono text-xs font-semibold text-primary">
          IW
        </div>
        {!collapsed ? (
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold tracking-tight">IncidentWeave</p>
            <p className="truncate text-[11px] text-muted-foreground">Evaluation UI</p>
          </div>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            healthy === true && "bg-success",
            healthy === false && "bg-destructive",
            healthy == null && "bg-muted-foreground",
          )}
          aria-hidden
        />
        {!collapsed ? (
          <span className="text-xs text-muted-foreground">
            {healthy === true
              ? "API reachable"
              : healthy === false
                ? "API unreachable"
                : "Checking API…"}
          </span>
        ) : null}
        <div className="ml-auto flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onOpenSettings}
            aria-label="Open settings"
          >
            <Settings2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {!collapsed ? (
        <>
          <section className="border-b border-border px-3 py-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                Repositories
              </h2>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onRefreshRepositories}
                aria-label="Refresh repositories"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
            <div className="grid max-h-40 gap-1 overflow-auto pr-1">
              {repositories.length === 0 ? (
                <p className="text-xs text-muted-foreground">No repositories loaded.</p>
              ) : (
                repositories.map((repo) => (
                  <button
                    key={repo.name}
                    type="button"
                    onClick={() => onSelectRepository(repo.name)}
                    className={cn(
                      "rounded-md px-2 py-1.5 text-left transition-colors",
                      repositoryName === repo.name
                        ? "bg-primary/15 text-foreground"
                        : "hover:bg-accent",
                    )}
                  >
                    <p className="truncate font-mono text-xs">{repo.name}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {repo.embedded_chunk_count}/{repo.chunk_count} embedded
                    </p>
                  </button>
                ))
              )}
            </div>
          </section>

          <section className="flex min-h-0 flex-1 flex-col px-3 py-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                History
              </h2>
              <span className="text-[11px] text-muted-foreground">{history.length}</span>
            </div>
            <div className="min-h-0 flex-1 space-y-1 overflow-auto pr-1">
              {history.length === 0 ? (
                <p className="text-xs text-muted-foreground">
                  Completed investigations will appear here.
                </p>
              ) : (
                history.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => onSelectInvestigation(item.id)}
                    className={cn(
                      "w-full rounded-md border px-2 py-1.5 text-left transition-colors",
                      activeId === item.id
                        ? "border-primary/40 bg-primary/10"
                        : "border-transparent hover:border-border hover:bg-accent",
                    )}
                  >
                    <div className="mb-1 flex items-center gap-1.5">
                      <Badge variant="outline">{item.outcome}</Badge>
                      <span className="font-mono text-[10px] text-muted-foreground">
                        #{item.id}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-xs leading-snug">{truncate(item.query, 90)}</p>
                    <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                      {formatLatency(item.latency_ms)} · {item.created_at}
                    </p>
                  </button>
                ))
              )}
            </div>
            {hasMoreHistory ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="mt-2"
                disabled={historyLoading}
                onClick={onLoadMoreHistory}
              >
                {historyLoading ? "Loading…" : "Load more"}
              </Button>
            ) : null}
          </section>
        </>
      ) : null}
    </aside>
  );
}
