import { defineConfig } from "astro/config"

export default defineConfig({
  site: "https://www.kschaul.com",
  // Files in static/ are copied as-is to the site root.
  publicDir: "static",
  outDir: "dist",
  trailingSlash: "ignore",
})
