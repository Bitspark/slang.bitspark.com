# Slang website

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Bitspark/slang-design/a16912ee2938ad9202380c88ce486adf893e5ccf/assets/logo/slang-logo-dark.svg">
    <img src="https://raw.githubusercontent.com/Bitspark/slang-design/a16912ee2938ad9202380c88ce486adf893e5ccf/assets/logo/slang-logo-light.svg" alt="Slang" width="280">
  </picture>
</p>

The public Slang product website at **https://slang.bitspark.com**. Built with
[Slang Design](https://github.com/Bitspark/slang-design): petrol and raspberry,
Roboto and Roboto Slab, transparent theme-specific logos, and typed connections.

## Repository boundaries

| Repository | Responsibility |
| --- | --- |
| [slang.bitspark.com](https://github.com/Bitspark/slang.bitspark.com) | Product website and hosted studio quick start |
| [slang.run](https://github.com/Bitspark/slang.run) | Cloud application frontend, intended for `slang.run` |
| [slang-ui](https://github.com/Bitspark/slang-ui) | Released Angular playground editor |
| [slang-design](https://github.com/Bitspark/slang-design) | Shared design tokens, CSS recipes, components, fonts, and logos |
| [slang](https://github.com/Bitspark/slang) | Language runtime, daemon and workspace gateway |

The production studio is at `https://slang.run/`: account-based editing and
private tests, with public program endpoints on `slangapps.com`. The product
pages and quick start describe that flow. `tryslang.com` redirects to the product
site.

This repository contains product pages only. The presentation adapter that gave
the retired Angular playground this site's appearance now lives in
`slang-infra/deploy/public/compat`, beside the installer that applies it. It is
not part of releases from v0.3.0 onward.

## Develop

Requires Python 3.10+. No npm build or third-party Python package is needed.

```sh
python tools/build.py
python -m unittest discover -s tests -v
python -m http.server 5177 --bind 127.0.0.1 --directory dist/site
```

Open http://127.0.0.1:5177. Rebuild after source changes. The landing page and
guide are fully static.

`design-system.lock.json` pins an immutable Slang Design commit and archive
SHA-256. The build verifies it, then copies its unmodified `styles/`,
`components/`, and `assets/` together. That preserves font paths and includes
all upstream license notices. Product-page fonts and logos are self-hosted.
Product CSS defines layout; it does not carry a duplicate palette or a fork of
the design-system recipes.

The design directory installed by a release is what the retired playground's
adapter links its shared styles and logos from. Changing the pinned design
version therefore changes the paths that installation resolves, which it does
by reading the version out of the installed release.

## Verify and release

Before a release, check light/dark themes, logos, narrow layouts, theme
persistence, keyboard focus and the studio links. Follow the quick start against
the actual studio: signup, save recovery code, create Echo, Test, Submit, then
deploy in HTTP mode. Build tests verify resource references and upstream assets.

Open a PR for changes, pass CI, and merge to `main`. Update `website.json` and
tag `v<version>` for releases. The workflow publishes a reproducible ZIP and
SHA-256 file; release tags must not be moved. The ZIP contains `site/` and
licenses. It contains no backend, credentials, or visitor data.

Production deployment is owned by `slang-infra/deploy/cloud`: the product site
is a static Caddy site on `slang-app`. Its release manifest pins the website
revision and artifact hash. The retired `slang-infra/deploy/public` playground
keeps its own website lock for older standalone installations; it is no longer
the active product site deployment. Update that lock after publishing a
reviewed release here.

New code: Apache-2.0. See [NOTICE](NOTICE) for origin and dependency attribution.
