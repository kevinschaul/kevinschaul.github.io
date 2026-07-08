import { getCollection } from "astro:content"
import { collectTags } from "@/lib/collections"
import { getAllFeedEntries, type FeedEntry } from "@/lib/rss"
import { absoluteUrl, entryPath } from "@/lib/site"
import { hugoDateParts, tagPath } from "@/lib/urls"

// Mirrors Hugo's sitemap: home, top-level pages, section indexes, entries,
// and tag pages — no /page/N/ URLs

interface SitemapUrl {
  loc: string
  lastmod?: string
}

function lastmod(raw: string | Date | undefined): string | undefined {
  return hugoDateParts(raw)?.date.toISOString()
}

function newest(entries: FeedEntry[]): string | Date | undefined {
  return entries[0]?.data.date
}

export async function GET() {
  const entries = await getAllFeedEntries()
  const pages = (await getCollection("page")).filter(
    (entry) => entry.id !== "_index",
  )
  const tags = collectTags(entries)

  const urls: SitemapUrl[] = [
    { loc: "/", lastmod: lastmod(newest(entries)) },
    ...pages.map((entry) => ({ loc: `/${entry.id}/` })),
    ...(["post", "til", "link", "project"] as const).map((section) => ({
      loc: `/${section}/`,
      lastmod: lastmod(newest(entries.filter((e) => e.collection === section))),
    })),
    ...entries.map((entry) => ({
      loc: entryPath(entry),
      lastmod: lastmod(entry.data.date),
    })),
    { loc: "/tags/", lastmod: lastmod(newest(entries)) },
    ...[...tags.keys()].map((tag) => ({
      loc: tagPath(tag),
      lastmod: lastmod(
        newest(
          entries.filter((e) =>
            (e.data.tags ?? []).some((t) => t?.toLowerCase() === tag),
          ),
        ),
      ),
    })),
  ]

  const xml =
    `<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls
      .map(
        ({ loc, lastmod }) =>
          `  <url>\n    <loc>${absoluteUrl(loc)}</loc>\n` +
          (lastmod ? `    <lastmod>${lastmod}</lastmod>\n` : "") +
          `  </url>`,
      )
      .join("\n") +
    `\n</urlset>\n`

  return new Response(xml, {
    headers: { "Content-Type": "application/xml" },
  })
}
