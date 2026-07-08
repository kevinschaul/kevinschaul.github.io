import type { APIContext } from "astro"
import { sectionFeed } from "@/lib/rss"

export async function GET(context: APIContext) {
  return sectionFeed(context, "project")
}
