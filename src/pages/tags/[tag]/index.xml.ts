import rss from "@astrojs/rss"
import { getCollection } from "astro:content"
import type { APIContext } from "astro"
import { collectTags, sortByDateDesc } from "@/lib/collections"
import { SITE } from "@/lib/site"
import { feedOptions, getAllFeedEntries } from "@/lib/rss"
import { urlize } from "@/lib/urls"

export async function getStaticPaths() {
  const tags = collectTags(await getAllFeedEntries())
  return [...tags.entries()].map(([tag, { title }]) => ({
    params: { tag: urlize(tag) },
    props: { tag, title },
  }))
}

export async function GET(context: APIContext) {
  const { tag, title } = context.props as { tag: string; title: string }
  const allEntries = [
    ...(await getCollection("post")),
    ...(await getCollection("til")),
    ...(await getCollection("link")),
    ...(await getCollection("project")),
  ]
  const entries = sortByDateDesc(
    allEntries.filter((entry) =>
      (entry.data.tags ?? []).some((entryTag) => entryTag?.toLowerCase() === tag),
    ),
  )

  return rss(
    feedOptions(
      context,
      `${title} on ${SITE.title}`,
      `Recent content tagged ${title} on ${SITE.title}`,
      entries,
    ),
  )
}
