---
title: Mock fs with vitest and memfs
date: 2024-06-26
slug: mock-fs-with-vitest-and-memfs
tags: [nodejs]
---

I’ve been using [vitest](vitest) for testing node code lately, and I often want
to set up a fake file system. I’d been using
[mockFS](https://github.com/tschaub/mock-fs) for this, which is no longer
maintained. Fortunately [memfs](https://github.com/streamich/memfs) is a
drop-in alternative — if you know this secret: You’ve got to add a mock fs
call.

```
import { vol, fs } from "memfs";
import { vi, describe, test, expect, beforeEach, afterEach } from "vitest";

// Mock fs everywhere else with the memfs version.
vi.mock("fs", async () => {
  const memfs = await vi.importActual("memfs");

  // Support both `import fs from "fs"` and "import { readFileSync } from "fs"`
  return { default: memfs.fs, ...memfs.fs };
});
```

Then, you can set up a fake filesystem for your test:

```
describe('my-suite', () => {
  afterEach(() => {
    vol.reset();
  });

  ...

  test('same dir', async () => {
    vol.fromNestedJSON({
      '/Users/username/my-package': {
        'package.json': '{}',
        styles: {
          subdir: {
            'package.json': '{}',
          },
        },
      },
    });

    ...
  });
})
```

Thank you so much [for this
comment](https://github.com/tschaub/mock-fs/issues/384#issuecomment-2173802850),
bcass.
