export function buildGithubUrl(
  baseUrl: string | undefined,
  filePath: string,
  startLine: number | null | undefined,
  endLine: number | null | undefined,
): string | null {
  const base = (baseUrl || "").trim().replace(/\/+$/, "");
  if (!base || !filePath) return null;

  const path = filePath.replace(/^\/+/, "");
  let url = `${base}/blob/main/${path}`;
  if (startLine != null) {
    url += `#L${startLine}`;
    if (endLine != null && endLine !== startLine) {
      url += `-L${endLine}`;
    }
  }
  return url;
}

export function formatLineRange(
  startLine: number | null | undefined,
  endLine: number | null | undefined,
): string {
  if (startLine == null && endLine == null) return "—";
  if (startLine != null && endLine != null && startLine !== endLine) {
    return `L${startLine}–${endLine}`;
  }
  return `L${startLine ?? endLine}`;
}
