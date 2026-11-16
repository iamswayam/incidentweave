import { useCallback, useState } from "react";

const SETTINGS_KEY = "iw.settings";

export interface AppSettings {
  apiBase: string;
  apiSecret: string;
  githubBaseUrl: string;
}

const DEFAULTS: AppSettings = {
  apiBase: "",
  apiSecret: "",
  githubBaseUrl: "",
};

function readSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw) as Partial<AppSettings>;
    return {
      apiBase: typeof parsed.apiBase === "string" ? parsed.apiBase : "",
      apiSecret: typeof parsed.apiSecret === "string" ? parsed.apiSecret : "",
      githubBaseUrl:
        typeof parsed.githubBaseUrl === "string" ? parsed.githubBaseUrl : "",
    };
  } catch {
    return { ...DEFAULTS };
  }
}

export function useSettings() {
  const [settings, setSettingsState] = useState<AppSettings>(() => readSettings());

  const saveSettings = useCallback((next: AppSettings) => {
    setSettingsState(next);
    try {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }, []);

  return { settings, saveSettings };
}
