# Slang website

The public Slang product website at **https://slang.bitspark.com**. Built with
[Slang Design](https://github.com/Bitspark/slang-design): petrol and raspberry,
Roboto and Roboto Slab, transparent theme-specific logos, and typed connections.

## Repository boundaries

| Repository | Responsibility |
| --- | --- |
| [slang.bitspark.com](https://github.com/Bitspark/slang.bitspark.com) | Product website, quick start, and presentation adapter for the restored public playground |
| [slang.run](https://github.com/Bitspark/slang.run) | Cloud application frontend, intended for `slang.run` |
| [slang-ui](https://github.com/Bitspark/slang-ui) | Released Angular playground editor |
| [slang-design](https://github.com/Bitspark/slang-design) | Shared design tokens, CSS recipes, components, fonts, and logos |
| [slang](https://github.com/Bitspark/slang) | Language runtime, workspace gateway, and production infrastructure |

The working playground remains at `tryslang.com/app/` while the cloud frontend
is restored. Existing browser workspace cookies stay on that origin. Product
pages link to the working playground; move those links to `slang.run` when its
actual application is ready. Do not substitute a static design specimen for it.

## Develop

Requires Python 3.10+. No npm build or third-party Python package is needed.

```sh
python tools/build.py
python -m unittest discover -s tests -v
python -m http.server 5177 --bind 127.0.0.1 --directory dist/site
```

Open http://127.0.0.1:5177. Rebuild after source changes. The landing page and
guide are fully static; the editor adapter is verified against the released
Angular editor by the runtime repository's public deployment.

`design-system.lock.json` pins an immutable Slang Design commit and archive
SHA-256. The build verifies it, then copies its unmodified `styles/`,
`components/`, and `assets/` together. That preserves font paths and includes
all upstream license notices. No third-party font or logo requests are made.
Product CSS defines layout and maps legacy editor selectors to semantic tokens;
it does not carry a duplicate palette or a fork of the design-system recipes.

`site/assets/editor.js` adds the shared control recipes and accessible names to
native Angular controls. It does not replace event handlers, compile or execute
programs, change API routes, or access application state. The old editor exposes
port types, but no connection type in its DOM: ports keep exact type colors;
connections use the design system's generic wire color.

## Verify and release

Before a release, check light/dark themes, transparent logos, narrow layouts,
theme persistence, keyboard focus, search, program creation/save/reload, and a
real run: **Double a number → Run → 21 → Send → 42 → Stop**. Check YAML and
workspace import/export too. Build tests follow HTML/CSS/font asset references
and verify that every shipped Slang Design byte matches upstream.

Open a PR for changes, pass CI, and merge to `main`. Update `website.json` and
tag `v<version>` for releases. The workflow publishes a reproducible ZIP and
SHA-256 file; release tags must not be moved. The ZIP contains `site/`,
`editor-head.html`, `editor-shell.html`, and licenses. It contains no backend,
credentials, or visitor data.

Deployment is owned by `slang/deploy/public`: update its `website.lock.json` to
the release URL and checksum, then use its frontend-only installer. Website
updates do not restart active programs. The runtime repository keeps the pinned
version and rollback instructions; website changes no longer live there.

New code: Apache-2.0. See [NOTICE](NOTICE) for origin and dependency attribution.
