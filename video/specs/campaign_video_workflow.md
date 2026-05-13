# Campaign Video Workflow (MVP)

## Flow

1. Define campaign input (book metadata or LinkedIn post).
2. Generate Hook.
3. Generate `SCRIPT.md`.
4. Convert script into `STORYBOARD.md`.
5. Create/update `DESIGN.md`.
6. Generate HyperFrames `composition.html`.
7. Render MP4 via `scripts/render_video.sh`.
8. Review and publish as campaign asset.
9. Record outcomes in DMN memory and campaign logs.

## Outputs

- reusable composition templates
- renderable MP4 assets in `video/renders/`
- campaign-friendly script/storyboard/design artifacts

## Guardrails

- local-first workflow
- no external API requirement
- no autonomous posting automation
- keep compatibility with existing Hermes/Guardian boundaries
