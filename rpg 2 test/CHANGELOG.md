# Changelog

All notable changes to Shattered Marches will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-11-23

### Added
- PyQt6 desktop game launcher and native game window.
- World map, town, quest, arena, combat, save, and load systems.
- Procedural pixel-art sprites and battle impact effects.
- Automated coverage for GUI rendering, world movement, battles, quests, jobs,
  arena encounters, and world events.

### Fixed
- Completed an end-to-end smoke test of launcher startup and CLI entry.
- Confirmed the complete automated test suite passes without crashes.

### Testing
- Ran 10 shuffled permutations of all 33 tests with seeds 202601 through 202610.
- Every permutation passed; no game or test-process crashes were observed.
- Ran the battle-only suite 10 times with seeds 2026101 through 2026110.
- All 7 battle tests passed in every run; no fight-system crashes were observed.
- Added playable character races and race-derived stat bonuses.
- Added a custom class option with point-buy characteristics and starting abilities.
- Preserved custom classes, races, and custom starting abilities in save data.
- Fixed negative race modifiers from producing invalid MP or characteristic totals.
- Tested 50 custom-class/race/ability permutations; all built valid four-member parties
  without crashes.
- Added base-class templates: Fighter, Thief, Paladin, Red Mage, and Archmage.
- Added no/low/medium/full magic tiers with maximum spell levels and per-level spell slots.
- Added custom spell and ability registration APIs with level-based learning support.
- Expanded equipment to weapon, armor, helm, and two accessory slots.
- Added a CLI story authoring tool for reusable story, quest, act, and event templates.
- Expanded the overworld to 30 x 30 tiles across six named regions.
- Synchronized world event markers with the enlarged map and added story-tool tests.
- Added 36 enemy types with 10 power variations each.
- Added elemental affinities, strengths, and weaknesses through a shared balance matrix.
- Added a level-based guild Blacksmith for custom weapons and armor.
- Added six weapon templates, four armor templates, and six crafting materials.
- Expanded crafting into a multi-material pipeline with shop, mine, wild, enemy-drop,
  and component-crafting acquisition sources.
- Added blade/core/binding and plate/lining/enchantment placement bonuses.
- Completed 10 full-suite permutations with seeds 20261301 through 20261310.
- All 48 tests passed in every run; no crashes or unexpected process exits were observed.
- Launcher startup and CLI quit smoke checks passed.
- Added customizable strongholds: Hideout, Fortress, Temple, Academy, and Estate.
- Added an exactly 200-entry stronghold improvement catalog with type compatibility,
  prerequisites, costs, levels, passive bonuses, and save/load support.
- Added skill points based on magic tier: no magic 6, low 4, medium 3, full 2.
- Added level-gated skill trees, prerequisite learning, power scaling, and custom
  skill-tree creation.
- Learned skills are combat abilities and preserve through save/load.
- Added an Android-compatible installable PWA with touch controls and a mobile API.
- Added mobile movement, combat, party, new-game, save, and load actions.
- Added a native Android/Chaquopy Gradle project and WebView launcher.
- Added a GitHub Actions workflow that builds and uploads a debug APK.
