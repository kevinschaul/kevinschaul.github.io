import rss from "@astrojs/rss"
import type { APIContext } from "astro"
import { SITE } from "../../lib/site"
import { feedOptions, getSectionFeedEntries, SECTION_TITLES } from "../../lib/rss"

export async function GET(context: APIContext) {
  const entries = await getSectionFeedEntries("til")
  return rss(
    feedOptions(
      context,
      `${SECTION_TITLES.til} on ${SITE.title}`,
      `Recent ${SECTION_TITLES.til} on ${SITE.title}`,
      entries,
    ),
  )
}
