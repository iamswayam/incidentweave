import { useEffect, useState } from "react";
import type { AppSettings } from "@/hooks/useSettings";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

interface SettingsDialogProps {
  open: boolean;
  settings: AppSettings;
  onOpenChange: (open: boolean) => void;
  onSave: (settings: AppSettings) => void;
}

export function SettingsDialog({
  open,
  settings,
  onOpenChange,
  onSave,
}: SettingsDialogProps) {
  const [draft, setDraft] = useState(settings);

  useEffect(() => {
    if (open) setDraft(settings);
  }, [open, settings]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Local-only connection settings. Secrets stay in this browser.
          </DialogDescription>
        </DialogHeader>
        <form
          className="grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            onSave(draft);
            onOpenChange(false);
          }}
        >
          <label className="grid gap-1.5 text-sm">
            <span className="text-muted-foreground">API base URL</span>
            <Input
              value={draft.apiBase}
              placeholder="Leave empty to use /api proxy"
              onChange={(event) =>
                setDraft((current) => ({ ...current, apiBase: event.target.value }))
              }
            />
          </label>
          <label className="grid gap-1.5 text-sm">
            <span className="text-muted-foreground">X-API-Secret</span>
            <Input
              type="password"
              autoComplete="off"
              value={draft.apiSecret}
              placeholder="Required when the backend enforces auth"
              onChange={(event) =>
                setDraft((current) => ({ ...current, apiSecret: event.target.value }))
              }
            />
          </label>
          <label className="grid gap-1.5 text-sm">
            <span className="text-muted-foreground">GitHub repo URL</span>
            <Input
              value={draft.githubBaseUrl}
              placeholder="https://github.com/org/repo"
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  githubBaseUrl: event.target.value,
                }))
              }
            />
          </label>
          <div className="mt-1 flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Save</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
