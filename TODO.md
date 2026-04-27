# Goose Goose Duck AI Bot TODO

## Project Guardrails

- [ ] Use only in private friend rooms where everyone knows an AI is filling a seat.
- [ ] Do not use memory reading, packet inspection, process injection, or anti-cheat bypasses.
- [ ] Keep the bot visibly identified, for example with a name like `AI_Bot`.
- [ ] Add a global emergency stop before enabling any automatic input.
- [ ] Pause automatically when the game window is not focused or the UI is unknown.

## Phase 1: Coach Prototype

- [x] Create a Python desktop process scaffold for the read-only Coach.
- [x] Replace slow debug-only screenshots with a faster in-memory capture path.
- [x] Capture the Goose Goose Duck window instead of the full desktop when a matching window title is available.
- [x] Add a continuous in-memory preview loop with FPS display.
- [ ] Detect high-level game states: lobby, free movement, meeting, voting, death/ghost, unknown.
- [ ] Add OCR for visible task text and meeting/voting player names.
- [ ] Add speech-to-text for friend-room discussion.
- [ ] Save a timestamped round log in JSONL or SQLite.
- [ ] Generate meeting suggestions: ask a question, skip vote, vote for a named player, or state insufficient information.

## Phase 2: Game Memory

- [ ] Track player status: alive/dead/unknown.
- [ ] Track sightings: player, location, timestamp, confidence.
- [ ] Track claims from meetings and chat.
- [ ] Detect simple contradictions between sightings and claims.
- [ ] Produce a concise suspicion summary after each meeting.

## Phase 3: Private-Room Movement

- [ ] Build a simple map graph for the first supported map.
- [ ] Define key locations: spawn, task points, meeting button, common rooms, corridors.
- [ ] Implement keyboard/mouse control only when the game window is active.
- [ ] Add stuck detection and recovery.
- [ ] Add manual approval mode before full automation.

## Phase 4: Basic Goose Gameplay

- [ ] Navigate to nearby task points.
- [ ] Complete only simple click/wait tasks at first.
- [ ] Report bodies when clearly detected.
- [ ] Avoid following one suspicious player alone.
- [ ] Attend meetings and vote according to structured AI output.

## Phase 5: Friend-Room Automation

- [ ] Add a pre-game consent checklist for all players.
- [ ] Run several short private-room tests with manual takeover ready.
- [ ] Log every AI action and reason.
- [ ] Review failure cases after each session.
- [ ] Decide whether to add text chat or voice output.

## Backlog

- [ ] Build a small replay viewer for screenshots, transcripts, and decisions.
- [ ] Add support for more maps.
- [ ] Add role-specific strategy modules.
- [ ] Build a simplified simulator for testing decisions without connecting to real games.
- [ ] Add a configuration UI for hotkeys, capture region, model choice, and safety limits.
