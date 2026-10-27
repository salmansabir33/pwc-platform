# Shared web design tokens

W1 semantic colors, typography fallback stacks, spacing, radii and focus colors live in `tokens.css`. Both portals consume the same tokens; their scoped accent overrides do not imply permissions. The unmodified Noto Sans Arabic variable Arabic subset is self-hosted from pinned Fontsource 5.3.0 (OFL-1.1); its copyright/license notice is copied into both builds via the shared public directory. No remote font service is used. Native-language/font readability review remains release work.

These are CSS foundations, not shared Dart widgets or approval of a complete brand system. See the [web foundation runbook](../../docs/runbooks/PWC-W1-WEB-FOUNDATION.md).

## v1.0 stable semantic contract

Authority: [approved visual standard](../../docs/design/PWC_DESIGN_SYSTEM_v1.0.md).
`tokens.v1.json` is the versioned, platform-neutral source. Run
`python3 scripts/design_tokens.py` after approved changes; `npm run tokens:check`
checks the CSS and Dart adapters (Dart whitespace ignored, string contents preserved).
`--ds-*` values are public v1 semantics; existing `--color-*`, `--space-*` and
`--radius-*` aliases remain compatible. Do not rename meanings in-place.
Flutter consumes `PwcTokens` through `pwcTheme`, not React CSS or runtime imports.

Derived defaults: info/restricted use Operations blue on `#EEF1F8` (text must
say which state applies); success `#EAF5EF`, warning `#FFF4DF`, danger `#FDEEEB`.
Brand hover/pressed are darkened independently; disabled uses `#52636B` on
`#E8EDED`, not transparency. Selection uses each brand's status background and
primary text; status never implies server-issued authority. Borders `#D8E1E2`
are decorative; interactive boundaries use `#72848A` for at least 3:1 contrast.
Focus is 3px `#AD480A` with 4px web offset; native uses a 3px focus border.
Elevations and 45% dialog overlay are centralized in tokens.css/shared styles;
no animation is required. Dark themes/charts remain deferred.

Fonts are local assets under OFL-1.1, never downloaded at runtime. Inter variable
TTF is identical in web public assets and mobile. Existing pinned Fontsource
Noto Sans Arabic Variable WOFF2 remains web's Arabic subset; native uses the
Google Fonts full variable TTF. `font-provenance.json` records immutable Git
blobs, hashes and sizes; both licenses accompany native files, Inter's license
accompanies web files, and the existing Arabic license accompanies web builds.
Different subset/rendering engines require native Urdu typography acceptance;
this does not claim exact glyph parity or complete translation coverage.
