import { defineCollection, z } from "astro:content"
import { glob } from "astro/loaders"

// Keep collection IDs unique. Public URLs still mirror Hugo's :slug behavior
// in src/lib/site.ts, where frontmatter `slug` wins.
const keepName = ({ entry }: { entry: string; data: Record<string, unknown> }) =>
  entry.replace(/\/index\.md$/, "").replace(/\.md$/, "")

const common = z
  .object({
    title: z.string().nullable().default(""),
    // keep raw — URL parts depend on Hugo's naive-date semantics (urls.ts)
    date: z.union([z.string(), z.date()]).optional(),
    slug: z.string().optional(),
    draft: z.boolean().default(false),
    tags: z.array(z.string().nullable()).nullable().default([]),
    author: z.string().nullable().optional(),
    blurb: z.string().optional(),
    images: z.array(z.string()).default([]),
    resources: z
      .array(
        z.object({
          src: z.string(),
          params: z.object({ alt: z.string().optional() }).optional(),
        }),
      )
      .optional(),
  })
  .passthrough()

const post = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./content/post", generateId: keepName }),
  schema: common,
})

const til = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./content/til", generateId: keepName }),
  schema: common,
})

const link = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./content/link", generateId: keepName }),
  schema: common.extend({
    images: z.array(z.string()).default([]),
  }),
})

const project = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./content/project", generateId: keepName }),
  schema: common.extend({
    external_url: z.string().optional(),
    weight: z.number().optional(),
  }),
})

// Top-level pages: contact.md, follow.md, _index.md (home intro)
const page = defineCollection({
  loader: glob({ pattern: "*.md", base: "./content" }),
  schema: common,
})

export const collections = { post, til, link, project, page }
