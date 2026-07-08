import rss from "@astrojs/rss"
import type { APIContext } from "astro"
import { SITE } from "../../lib/site"
import { feedOptions, getSectionFeedEntries, SECTION_TITLES } from "../../lib/rss"

export async function GET(context: APIContext) {
  const entries = await getSectionFeedEntries("post")
  return rss(
    feedOptions(
      context,
      `${SECTION_TITLES.post} on ${SITE.title}`,
      `Recent ${SECTION_TITLES.post.toLowerCase()} on ${SITE.title}`,
      entries,
    ),
  )
}
