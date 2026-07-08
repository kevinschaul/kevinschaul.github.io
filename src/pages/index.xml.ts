import rss from "@astrojs/rss"
import type { APIContext } from "astro"
import { SITE } from "../lib/site"
import { feedOptions, getAllFeedEntries } from "../lib/rss"

export async function GET(context: APIContext) {
  const entries = await getAllFeedEntries()
  return rss(feedOptions(context, SITE.title, SITE.description, entries))
}
