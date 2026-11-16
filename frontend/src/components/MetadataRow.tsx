import { Check, Copy } from "lucide-react";
import { useState } from "react";
import type { InvestigationResponse } from "@/api/types";
import { Button } from "@/components/ui/button";

interface MetadataRowProps {
  result: InvestigationResponse;
}

export function MetadataRow({ result }: MetadataRowProps) {
  const [copied, setCopied] = useState(false);

  async function copyJson() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="animate-fade-in flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card px-4 py-3">
      <dl className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <div className="flex gap-1.5">
          <dt>Model</dt>
          <dd className="font-mono text-foreground">{result.model || "—"}</dd>
        </div>
        <div className="flex gap-1.5">
          <dt>Investigation</dt>
          <dd className="font-mono text-foreground">
            {result.investigation_id ?? "—"}
          </dd>
        </div>
        <div className="flex gap-1.5">
          <dt>Repository</dt>
          <dd className="font-mono text-foreground">{result.repository_name}</dd>
        </div>
      </dl>
      <Button type="button" variant="outline" size="sm" onClick={copyJson}>
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        {copied ? "Copied" : "Copy JSON"}
      </Button>
    </section>
  );
}
