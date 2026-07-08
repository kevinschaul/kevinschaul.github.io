import { defineConfig } from "astro/config"
import { remarkYoutubeEmbed } from "./src/lib/remark-youtube-embed.ts"

export default defineConfig({
  site: "https://www.kschaul.com",
  // Files in static/ are copied as-is to the site root.
  publicDir: "static",
  outDir: "dist",
  trailingSlash: "ignore",
  markdown: {
    remarkPlugins: [remarkYoutubeEmbed],
  },
})
