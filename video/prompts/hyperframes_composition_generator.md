# Prompt: HyperFrames Composition Generator

## Input

- Storyboard
- Design notes
- Brand assets path

## Task

產生可 render 的 `composition.html`，符合：

- root element 包含 `data-composition-id`, `data-width`, `data-height`
- 每段畫面為 `.clip`，含 `data-start`, `data-duration`, `data-track-index`
- 使用 GSAP timeline，`paused: true`
- timeline 註冊到 `window.__timelines`
- 預設 1080x1080, 30fps

## Constraints

- Plain HTML/CSS/JS only
- No React, No Remotion
- No external API dependency
