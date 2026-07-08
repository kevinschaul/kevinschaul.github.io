// Approximations of Hugo's .Summary and .WordCount for meta tags

function plainText(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\{\{<[^>]*>\}\}/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/[#*_`>]/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{2,}/g, "\n")
    .trim()
}

// Hugo .Summary: first 70 words of the content's plain text
export function summarize(md: string): string {
  const text = plainText(md)
  const words = text.split(/\s+/)
  if (words.length <= 70) return text
  return words.slice(0, 70).join(" ")
}

export function countWords(md: string): number {
  const text = plainText(md)
  return text ? text.split(/\s+/).length : 0
}

// ISO timestamp for article meta. Offset-carrying dates pass through;
// naive dates get a nominal Chicago offset (metadata only, not visible).
export function publishedISO(raw: string | Date | undefined): string {
  if (!raw) return ""
  if (raw instanceof Date) return raw.toISOString().replace(/\.\d+Z$/, "+00:00")
  const s = String(raw).trim()
  if (/[+-]\d{2}:?\d{2}$|Z$/.test(s)) return s
  const m = s.match(/^(\d{4}-\d{2}-\d{2})([ T](\d{2}:\d{2}(:\d{2})?))?/)
  if (!m) return s
  return `${m[1]}T${m[3] || "00:00:00"}-06:00`
}
