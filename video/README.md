# Hermes v2 Video-as-Code Module

This module provides a local-first, agent-editable, template-first video workflow for ebook marketing campaigns.

## Pipeline

Ebook → LinkedIn Post → Script → Storyboard → HyperFrames HTML Composition → MP4 → Campaign Asset

## Structure

- `templates/`: reusable HyperFrames-ready video templates
- `prompts/`: reusable Codex prompts for script/storyboard/composition generation
- `specs/`: workflow and schema definitions
- `examples/`: minimal working demo project
- `renders/`: local output MP4 files
- `assets/`: shared media assets (covers/logos/audio)

## Rendering

First run may require internet access because `npx` can download `hyperframes` on demand.

```bash
./scripts/render_video.sh video/examples/ai-second-brain-demo/composition.html video/renders/ai-second-brain-demo.mp4
```

## Constraints

- plain HTML/CSS/JS compositions
- GSAP timeline animation
- no React/Remotion/cloud runtime
- no external API key requirement
