# KRATOS logo files

Use these instead of redrawing the logo. Each file is made for one ground, because the cut-outs (the visor, the gap around the ring, the helmet behind the ring) are filled with that ground colour:

| Ground | Colour | Use |
|---|---|---|
| `dark` | `#070A17` deep space | website, dark slides |
| `navy` | `#0B1026` navy | panels, slides |
| `light` | `#F3F4F8` paper | print, documents |

On a photo or any other colour, place the logo on a plate of its ground colour.

- `kratos-lockup-stacked-on-*`: the full logo, mark above the name. Use it when it is at least 96 px wide.
- `kratos-lockup-horizontal-on-*`: mark beside the name, for headers.
- `kratos-mark-on-*`: the mark alone.
- `kratos-icon`: the mark on a deep-space square, for the GitHub organisation and app icons.
- `kratos-lockup-animated-on-dark.svg`: the website intro; it plays once.

`svg/` holds the masters; `png/` holds renders with a transparent background (1024 px wide; the horizontal lockups are 2048 px wide).

Red (`#EE1C2E`) appears only in the heartbeat line and the delta in the A.

## Rebuilding

```
python3 -I brand/make_logo.py --png
```

This rewrites every file here and also updates `assets/favicon.svg`, `assets/favicon.png`, `assets/apple-touch-icon.png` and the animated logo in `index.html`. Rendering the PNGs requires `google-chrome` or `chromium`.
