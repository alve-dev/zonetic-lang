<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/icons/svg/icon_zonetic_dark.svg">
  <img src="./assets/icons/svg/icon_zonetic.svg" width="300">
</picture>

# Zonetic Programming Language — Tree-Walker

A statically typed, expression-oriented language designed for robotics.

> **This repository contains the tree-walker interpreter version of Zonetic.**  
> The bytecode VM version will live in a separate repository once development begins.

## Status

> `v0.1.0` — first fully functional release.  
> Tree-walker interpreter complete. Function support coming in `v0.1.1`.

## Features

- Explicit mutability with `mut` / `inmut`
- Form-based control flow — `if form`, `while form`, `infinity form`
- Block expressions with `give`
- Rust-inspired error reporting with spans and Zonny
- Hybrid statement terminators — `;` or newline
- Type inference from first assignment
- Real mutability enforcement
- 32 errors and 6 warnings across all compiler phases

## Quick Look
```rust
mut counter: int = 0

while counter < 10 {
    counter += 1
    if counter == 5 {
        break
    }
}

inmut result: int = if counter == 5 {
    give counter * 2
} else {
    give 0
}

print "Result: ", result
```

## Documentation

> Full language documentation → [link here](https://github.com/alve-dev/zonetic-official-docs)

## Pipeline
```
source → lexer → normalizer → parser → semantic → interpreter
```

Each phase has its own indexed error codes — `E0xxx` lexer, `E1xxx` normalizer, `E2xxx` parser, `E3xxx` semantic, `E4xxx` runtime.

## Logo

The Zonetic logo is available in both SVG and PNG formats.

- **SVG** — vector format, scales to any size. Available in [`assets/icons/svg`](assets/icons/svg).  
  > On mobile, SVG files may require a dedicated app to open. If your device does not support SVG natively, any vector graphics viewer will work.
- **PNG** — raster format, works everywhere. Available in [`assets/icons/png/`](assets/icons/png/) in multiple sizes.

![Language](https://img.shields.io/badge/written%20in-Python-yellow)
[![Version](https://img.shields.io/badge/version-0--1--0-orange)](changelog.md)