import type { CollectionEntry } from "astro:content"
import { hugoDateParts } from "./urls"

type Sections = "post" | "til" | "link" | "project"
export type SectionEntry = CollectionEntry<Sections>

export function sortByDateDesc<T extends { data: { date?: string | Date } }>(
  entries: T[],
): T[] {
  return [...entries].sort((a, b) => {
    const da = hugoDateParts(a.data.date)?.date.getTime() ?? 0
    const db = hugoDateParts(b.data.date)?.date.getTime() ?? 0
    return db - da
  })
}

// Hugo lowercases taxonomy keys; the displayed title keeps the typed
// casing (preferring a cased variant when both "ai" and "AI" exist)
export function collectTags(
  entries: { data: { tags?: (string | null)[] | null } }[],
): Map<string, { title: string; count: number }> {
  const tags = new Map<string, { title: string; count: number }>()
  for (const entry of entries) {
    for (const tag of entry.data.tags ?? []) {
      if (!tag) continue
      const key = tag.toLowerCase()
      const existing = tags.get(key)
      if (existing) {
        existing.count++
        if (existing.title === key && tag !== key) existing.title = tag
      } else {
        tags.set(key, { title: tag, count: 1 })
      }
    }
  }
  return tags
}

export const PAGE_SIZE = 10

export function paginate<T>(entries: T[]): T[][] {
  const pages: T[][] = []
  for (let i = 0; i < entries.length; i += PAGE_SIZE) {
    pages.push(entries.slice(i, i + PAGE_SIZE))
  }
  return pages.length ? pages : [[]]
}

// getStaticPaths entries for /section/page/N/ (page 1 is the section index)
export function paginatedPaths<T>(entries: T[]) {
  const pages = paginate(entries)
  return pages.slice(1).map((items, index) => ({
    params: { page: String(index + 2) },
    props: { items, page: index + 2, totalPages: pages.length },
  }))
}
