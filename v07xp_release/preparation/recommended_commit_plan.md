# Recommended Commit Plan

1. Ensure index empty of runtime paths
2. `git add` all `must_commit_release` paths (128 top-level entries → expands to full tree)
3. Single commit: `feat: freeze v0.7 civilization governance lineage`
4. Post-commit audit under `v07xp_release/post_commit/`
