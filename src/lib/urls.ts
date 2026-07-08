/*
 * URL construction mirroring the Hugo site's permalink config exactly:
 *   post: /post/:year/:month/:day/:slug/
 *   til:  /til/:year/:month/:day/:slug/
 *   link, project: Hugo defaults (/section/:slug/)
 *   tags: /tags/:tag/
 *
 * Entry ids already resolve Hugo's :slug token (see content.config.ts).
 *
 * Date semantics match Hugo with timeZone=America/Chicago:
 *  - naive dates ("2023-03-21", "2014-03-29 17:37:02") are interpreted in
 *    the site TZ, so their literal Y-M-D parts are the URL parts
 *  - dates with an explicit offset are converted to America/Chicago
 */

export interface DateParts {
  y: string
  m: string
  d: string
  date: Date
}

const NAIVE_RE = /^(\d{4})-(\d{2})-(\d{2})([ T]\d{2}:\d{2}(:\d{2})?)?$/

export function hugoDateParts(raw: string | Date | undefined): DateParts | null {
  if (raw === undefined || raw === null || raw === "") return null

  if (raw instanceof Date) {
    // Already parsed by YAML (unquoted ISO date) — YAML treats naive dates
    // as UTC, so UTC parts equal the literal parts
    return {
      y: String(raw.getUTCFullYear()),
      m: pad(raw.getUTCMonth() + 1),
      d: pad(raw.getUTCDate()),
      date: raw,
    }
  }

  const s = String(raw).trim()
  const naive = s.match(NAIVE_RE)
  if (naive) {
    return {
      y: naive[1],
      m: naive[2],
      d: naive[3],
      date: new Date(`${naive[1]}-${naive[2]}-${naive[3]}T12:00:00Z`),
    }
  }

  // Explicit offset: convert to America/Chicago parts
  const date = new Date(s)
  const chicago = date.toLocaleDateString("en-CA", {
    timeZone: "America/Chicago",
  })
  const [y, m, d] = chicago.split("-")
  return { y, m, d, date }
}

function pad(n: number): string {
  return String(n).padStart(2, "0")
}

export function datedPath(
  section: string,
  id: string,
  rawDate: string | Date | undefined,
): string {
  const parts = hugoDateParts(rawDate)
  if (!parts) return `/${section}/${id}/`
  return `/${section}/${parts.y}/${parts.m}/${parts.d}/${id}/`
}

export function sectionPath(section: string, id: string): string {
  return `/${section}/${id}/`
}

export function tagPath(tag: string): string {
  // Hugo urlize: lowercase, spaces to hyphens
  return `/tags/${tag.toLowerCase().replace(/\s+/g, "-")}/`
}

// Hugo's :date_medium, e.g. "Apr 10, 2025"
export function formatDateMedium(rawDate: string | Date | undefined): string {
  const parts = hugoDateParts(rawDate)
  if (!parts) return ""
  return new Date(
    `${parts.y}-${parts.m}-${parts.d}T12:00:00Z`,
  ).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  })
}

// RFC 822 for RSS pubDate, rendered with the source offset intact is
// overkill — Hugo emits the stored zone; -0500/-0600 vs Z only shifts
// display. Use UTC consistently.
export function rfc822(rawDate: string | Date | undefined): string {
  const parts = hugoDateParts(rawDate)
  if (!parts) return ""
  const d = rawDate instanceof Date ? rawDate : new Date(String(rawDate))
  const valid = !isNaN(d.getTime()) ? d : parts.date
  return valid.toUTCString().replace("GMT", "+0000")
}
