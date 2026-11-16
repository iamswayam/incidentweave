import { useCallback, useEffect, useMemo, useState } from "react";
import {
  checkHealth,
  createInvestigation,
  getInvestigation,
  listInvestigations,
  listRepositories,
} from "@/api/client";
import { ApiError } from "@/api/types";
import type {
  InvestigationResponse,
  InvestigationSummary,
  RepositorySummary,
} from "@/api/types";
import { AnswerPanel } from "@/components/AnswerPanel";
import { ClaimsPanel } from "@/components/ClaimsPanel";
import { ErrorBanner } from "@/components/ErrorBanner";
import { MetadataRow } from "@/components/MetadataRow";
import { QueryPanel } from "@/components/QueryPanel";
import { ResultsSkeleton } from "@/components/ResultsSkeleton";
import { RetrievalBreakdown } from "@/components/RetrievalBreakdown";
import { SettingsDialog } from "@/components/SettingsDialog";
import { Sidebar } from "@/components/Sidebar";
import { useSettings } from "@/hooks/useSettings";
import { useTheme } from "@/hooks/useTheme";

const ACTIVE_REPO_KEY = "iw.activeRepository";
const SIDEBAR_KEY = "iw.sidebarCollapsed";

function readStoredString(key: string, fallback = ""): string {
  try {
    const value = localStorage.getItem(key);
    return typeof value === "string" ? value : fallback;
  } catch {
    return fallback;
  }
}

function readStoredBool(key: string, fallback = false): boolean {
  try {
    const value = localStorage.getItem(key);
    if (value === "true") return true;
    if (value === "false") return false;
    return fallback;
  } catch {
    return fallback;
  }
}

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const { settings, saveSettings } = useSettings();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    readStoredBool(SIDEBAR_KEY, false),
  );
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [repositories, setRepositories] = useState<RepositorySummary[]>([]);
  const [repositoryName, setRepositoryName] = useState(() =>
    readStoredString(ACTIVE_REPO_KEY),
  );
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [history, setHistory] = useState<InvestigationSummary[]>([]);
  const [hasMoreHistory, setHasMoreHistory] = useState(false);
  const [result, setResult] = useState<InvestigationResponse | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [bootstrapped, setBootstrapped] = useState(false);

  const apiSettings = useMemo(
    () => ({ apiBase: settings.apiBase, apiSecret: settings.apiSecret }),
    [settings.apiBase, settings.apiSecret],
  );

  const refreshHealth = useCallback(async () => {
    const ok = await checkHealth(apiSettings);
    setHealthy(ok);
    return ok;
  }, [apiSettings]);

  const refreshRepositories = useCallback(async () => {
    try {
      const rows = await listRepositories(apiSettings);
      setRepositories(rows);
      setRepositoryName((current) => {
        if (current && rows.some((row) => row.name === current)) return current;
        return rows[0]?.name ?? "";
      });
      setError(null);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Failed to load repositories.";
      setError(message);
      setRepositories([]);
    }
  }, [apiSettings]);

  const refreshHistory = useCallback(
    async (options: { append?: boolean; beforeId?: number } = {}) => {
      setLoadingHistory(true);
      try {
        const rows = await listInvestigations(apiSettings, {
          repository_name: repositoryName || undefined,
          limit: 20,
          before_id: options.beforeId,
        });
        setHistory((current) => (options.append ? [...current, ...rows] : rows));
        setHasMoreHistory(rows.length === 20);
        setError(null);
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Failed to load investigation history.";
        if (!options.append) setHistory([]);
        setHasMoreHistory(false);
        setError(message);
      } finally {
        setLoadingHistory(false);
      }
    },
    [apiSettings, repositoryName],
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, String(sidebarCollapsed));
    } catch {
      /* ignore */
    }
  }, [sidebarCollapsed]);

  useEffect(() => {
    try {
      if (repositoryName) localStorage.setItem(ACTIVE_REPO_KEY, repositoryName);
    } catch {
      /* ignore */
    }
  }, [repositoryName]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      await refreshHealth();
      if (cancelled) return;
      await refreshRepositories();
      if (cancelled) return;
      setBootstrapped(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshHealth, refreshRepositories]);

  useEffect(() => {
    if (!bootstrapped) return;
    void refreshHistory();
  }, [bootstrapped, repositoryName, refreshHistory]);

  async function handleSubmit() {
    if (!repositoryName || !query.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const response = await createInvestigation(apiSettings, {
        repository_name: repositoryName,
        query: query.trim(),
        limit,
      });
      setResult(response);
      setActiveId(response.investigation_id);
      await refreshHistory();
      await refreshHealth();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Investigation request failed.";
      setError(message);
      setHealthy(err instanceof ApiError && err.status === 0 ? false : healthy);
    } finally {
      setBusy(false);
    }
  }

  async function handleSelectInvestigation(id: number) {
    setBusy(true);
    setError(null);
    try {
      const response = await getInvestigation(apiSettings, id);
      setResult(response);
      setActiveId(id);
      setRepositoryName(response.repository_name);
      setQuery(response.query);
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Failed to load investigation.";
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      <Sidebar
        collapsed={sidebarCollapsed}
        theme={theme}
        healthy={healthy}
        repositories={repositories}
        repositoryName={repositoryName}
        history={history}
        activeId={activeId}
        historyLoading={loadingHistory}
        hasMoreHistory={hasMoreHistory}
        onToggleCollapsed={() => setSidebarCollapsed((value) => !value)}
        onToggleTheme={toggleTheme}
        onOpenSettings={() => setSettingsOpen(true)}
        onRefreshRepositories={() => {
          void refreshRepositories();
          void refreshHealth();
        }}
        onSelectRepository={setRepositoryName}
        onSelectInvestigation={(id) => {
          void handleSelectInvestigation(id);
        }}
        onLoadMoreHistory={() => {
          const last = history[history.length - 1];
          if (!last) return;
          void refreshHistory({ append: true, beforeId: last.id });
        }}
      />

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex items-center justify-between border-b border-border px-5 py-3">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
              Evaluation
            </p>
            <h1 className="text-lg font-semibold tracking-tight">
              {repositoryName || "Choose a repository"}
            </h1>
          </div>
          <p className="hidden text-xs text-muted-foreground md:block">
            Hybrid retrieval · grounded diagnosis · citation inspection
          </p>
        </header>

        <div className="min-h-0 flex-1 overflow-auto px-5 py-4">
          <div className="mx-auto grid max-w-6xl gap-4">
            <QueryPanel
              repositories={repositories}
              repositoryName={repositoryName}
              query={query}
              limit={limit}
              busy={busy}
              onRepositoryChange={setRepositoryName}
              onQueryChange={setQuery}
              onLimitChange={setLimit}
              onSubmit={() => {
                void handleSubmit();
              }}
            />

            {error ? (
              <ErrorBanner
                message={error}
                onRetry={() => {
                  if (result?.investigation_id) {
                    void handleSelectInvestigation(result.investigation_id);
                  } else if (query.trim()) {
                    void handleSubmit();
                  } else {
                    void refreshRepositories();
                    void refreshHistory();
                    void refreshHealth();
                  }
                }}
              />
            ) : null}

            {busy && !result ? <ResultsSkeleton /> : null}

            {result ? (
              <>
                <AnswerPanel result={result} />
                <ClaimsPanel
                  claims={result.claims || []}
                  evidence={result.evidence || []}
                  githubBaseUrl={settings.githubBaseUrl}
                />
                <RetrievalBreakdown
                  evidence={result.evidence || []}
                  citedChunkIds={result.cited_chunk_ids || []}
                />
                <MetadataRow result={result} />
              </>
            ) : !busy ? (
              <section className="rounded-lg border border-dashed border-border px-4 py-10 text-center">
                <p className="text-sm text-muted-foreground">
                  Run an investigation to inspect the diagnosis, claims, and retrieval
                  breakdown.
                </p>
              </section>
            ) : null}
          </div>
        </div>
      </main>

      <SettingsDialog
        open={settingsOpen}
        settings={settings}
        onOpenChange={setSettingsOpen}
        onSave={(next) => {
          saveSettings(next);
          const nextApi = { apiBase: next.apiBase, apiSecret: next.apiSecret };
          void (async () => {
            setHealthy(await checkHealth(nextApi));
            try {
              const rows = await listRepositories(nextApi);
              setRepositories(rows);
              setRepositoryName((current) => {
                if (current && rows.some((row) => row.name === current)) return current;
                return rows[0]?.name ?? "";
              });
              const historyRows = await listInvestigations(nextApi, {
                repository_name:
                  (repositoryName && rows.some((row) => row.name === repositoryName)
                    ? repositoryName
                    : rows[0]?.name) || undefined,
                limit: 20,
              });
              setHistory(historyRows);
              setHasMoreHistory(historyRows.length === 20);
              setError(null);
            } catch (err) {
              setError(
                err instanceof ApiError
                  ? err.message
                  : "Failed to reload after saving settings.",
              );
            }
          })();
        }}
      />
    </div>
  );
}
