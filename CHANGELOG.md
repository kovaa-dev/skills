# Changelog

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

No unreleased changes.

## [1.1.0](https://github.com/kovaa-dev/skills/compare/v1.0.0...v1.1.0) (2026-11-06)


### Features

* **dev-docs:** track requirement revision deliveries in queues ([9f828f1](https://github.com/kovaa-dev/skills/commit/9f828f1c5366bb0eb9b1f45fc3348b9b23127614))
* **dev-rules:** add reviews, visual verification, and programmatic access ([#32](https://github.com/kovaa-dev/skills/issues/32)) ([c5c3d9e](https://github.com/kovaa-dev/skills/commit/c5c3d9ea88d60c04fa34c0e8f37c7a4875ff3e3c))


### Bug Fixes

* **cost-audit:** read zstd session logs ([aed487f](https://github.com/kovaa-dev/skills/commit/aed487f6b6719a00f479a1d4ac3ae7b4c7f41a91))
* **dev-docs:** align requirement naming across guides and forms ([b4708f2](https://github.com/kovaa-dev/skills/commit/b4708f251e386a275ed3ab725efdf3e63fd72c2c))
* **dev-docs:** distinguish layer IDs from legacy document types ([168b773](https://github.com/kovaa-dev/skills/commit/168b773d4862c2d8f3a7f946bf10e59a39a2c3e1))
* **dev-docs:** make source transition schema independent ([ae0e6c3](https://github.com/kovaa-dev/skills/commit/ae0e6c3f83bb226e6cbae541746d2afdaaaf5537))
* **dev-docs:** mirror owner delivery status in queues ([505695a](https://github.com/kovaa-dev/skills/commit/505695af39ef86b9ce9da1aaab72c79924073f88))
* **dev-docs:** prefix layer requirement IDs with R ([3f21d1b](https://github.com/kovaa-dev/skills/commit/3f21d1bd054fd56239186d8a01add06b235749d5))
* **dev-docs:** preserve compatible routes and requirement identities ([ab30613](https://github.com/kovaa-dev/skills/commit/ab306137eb6333f5ce63dc8cca3c57823bc7d263))
* **dev-docs:** retain project layer ID namespaces ([8e3c7fc](https://github.com/kovaa-dev/skills/commit/8e3c7fc741ebf703bd42877e01c31d7dd8c532d5))
* **dev-docs:** reuse existing queues during legacy transition ([70677f5](https://github.com/kovaa-dev/skills/commit/70677f5c32cc63c58d9202e555486244bf42a37f))
* **dev-docs:** use linked queue rows and register useful outcomes ([c23e21c](https://github.com/kovaa-dev/skills/commit/c23e21c37c8034a84c7e8d18e60dd5003f94510c))
* **dev-rules:** bound MCP discovery ([55c8faa](https://github.com/kovaa-dev/skills/commit/55c8faaeac931cb8f779c5ba430d7213fea081f0))
* **dev-rules:** require explicit delivery authority ([#27](https://github.com/kovaa-dev/skills/issues/27)) ([1bdae11](https://github.com/kovaa-dev/skills/commit/1bdae118ae89ee67867335a0129a627fb8a00c9c))
* **dev-rules:** resolve audit contradictions ([#37](https://github.com/kovaa-dev/skills/issues/37)) ([a421184](https://github.com/kovaa-dev/skills/commit/a421184053c711b90a2f50f7782eb8c81b261c1e))


### Documentation

* **dev-docs:** group requirement context in wiki folders ([#35](https://github.com/kovaa-dev/skills/issues/35)) ([42954ea](https://github.com/kovaa-dev/skills/commit/42954ea44aafdde11068f3270624fa44ae13e320))
* **dev-docs:** keep requirements lean and embed research context ([8897600](https://github.com/kovaa-dev/skills/commit/88976003f695cb086d76120fea0a3c3c175e0a91))
* **dev-rules:** decouple documentation policy ([11c9300](https://github.com/kovaa-dev/skills/commit/11c9300a7268202d06a88fbe12359f7d2c09eb6b))
* **dev-rules:** refine branch name format ([eb4db69](https://github.com/kovaa-dev/skills/commit/eb4db69579bcd0063e5402fbacb083f8ea104589))
* **dev-rules:** standardize branch names ([cde8325](https://github.com/kovaa-dev/skills/commit/cde8325ba591a2de78676138a612e60691c8f872))

## [1.0.0](https://github.com/kovaa-dev/skills/compare/v0.5.0...v1.0.0) (2026-10-23)


### ⚠ BREAKING CHANGES

* **dev-docs:** PRD and layer-task authoring is legacy. Convert selected legacy work before continuation, or use migrate for a complete agreed scope.

### Features

* **dev-docs:** adopt requirements and work queues ([#25](https://github.com/kovaa-dev/skills/issues/25)) ([67f2d60](https://github.com/kovaa-dev/skills/commit/67f2d60ee6595585ac758504841d2e0382c70a0a))


### Bug Fixes

* brand skill display names ([#23](https://github.com/kovaa-dev/skills/issues/23)) ([a1cfa87](https://github.com/kovaa-dev/skills/commit/a1cfa87198495898963a0733b96b9db52f709f68))
* **doc-research:** preserve ordinary retrieval and automate reusable evidence memory ([#26](https://github.com/kovaa-dev/skills/issues/26)) ([f5ad04d](https://github.com/kovaa-dev/skills/commit/f5ad04d7e5d9a9eb317ada3127576262f401befe))

## [0.5.0](https://github.com/kovaa-dev/skills/compare/v0.4.3...v0.5.0) (2026-10-23)


### Features

* add research, cost audit, and orchestra skills ([#20](https://github.com/kovaa-dev/skills/issues/20)) ([d822429](https://github.com/kovaa-dev/skills/commit/d822429b8b5aada0401299816f853d14481058b1))


### Bug Fixes

* **cost-audit:** keep session evidence bounded and reproducible ([#22](https://github.com/kovaa-dev/skills/issues/22)) ([04b280a](https://github.com/kovaa-dev/skills/commit/04b280a21f1678a2c549a7a3f80b32ca17b6e5a3))

## [0.4.3](https://github.com/kovaa-dev/skills/compare/v0.4.2...v0.4.3) (2026-10-21)


### Documentation

* support existing projects and require MCP integrations ([#18](https://github.com/kovaa-dev/skills/issues/18)) ([0115c14](https://github.com/kovaa-dev/skills/commit/0115c1458f654187d31165294242c725fccfba3f))

## [0.4.2](https://github.com/kovaa-dev/skills/compare/v0.4.1...v0.4.2) (2026-10-20)


### Documentation

* focus tests and explanations on meaningful behavior ([#16](https://github.com/kovaa-dev/skills/issues/16)) ([bad7e14](https://github.com/kovaa-dev/skills/commit/bad7e1454f1579b432bf6702d2e7e29dd04ccc88))

## [0.4.1](https://github.com/kovaa-dev/skills/compare/v0.4.0...v0.4.1) (2026-10-14)


### Bug Fixes

* release skill documentation changes by default ([#14](https://github.com/kovaa-dev/skills/issues/14)) ([4d297b3](https://github.com/kovaa-dev/skills/commit/4d297b31060d9a752e5c4c4ddcf359001deff841))


### Documentation

* centralize measurement criteria and research lifecycle ([#13](https://github.com/kovaa-dev/skills/issues/13)) ([7c2d85c](https://github.com/kovaa-dev/skills/commit/7c2d85cdc91a41d6e493111e826b92eef41465ef))
* define deterministic worktree handoff ([#12](https://github.com/kovaa-dev/skills/issues/12)) ([3f942de](https://github.com/kovaa-dev/skills/commit/3f942de1a5fd9c4262b65e0894a3cb1898eef80e))
* standardize manual acceptance and workspaces in dev-rules ([#11](https://github.com/kovaa-dev/skills/issues/11)) ([5d0893e](https://github.com/kovaa-dev/skills/commit/5d0893eb2063a34b531e94e69cfce848b8db5731))

## [0.4.0](https://github.com/kovaa-dev/skills/compare/v0.3.1...v0.4.0) (2026-09-16)


### Features

* add grooming task lifecycle ([#10](https://github.com/kovaa-dev/skills/issues/10)) ([0d793e5](https://github.com/kovaa-dev/skills/commit/0d793e5ae667d8a01c3b91571454c1ddee4a8112))
* **dev-rules:** streamline PR publication ([#8](https://github.com/kovaa-dev/skills/issues/8)) ([96a0c31](https://github.com/kovaa-dev/skills/commit/96a0c3167a34382281ea3afc755b4058c34f7554))

## [0.3.1](https://github.com/kovaa-dev/skills/compare/v0.3.0...v0.3.1) (2026-09-12)


### Bug Fixes

* repair release validation and initial history ([#5](https://github.com/kovaa-dev/skills/issues/5)) ([cef5b49](https://github.com/kovaa-dev/skills/commit/cef5b49a080808fed1745b626b792b55eacf6fe6))

## [0.3.0](https://github.com/kovaa-dev/skills/compare/v0.2.0...v0.3.0) (2026-09-12)

### Added

- Added Release Please automation for synchronized version updates, changelog entries, Git tags, and GitHub Releases.

### Changed

- Moved development, validation, and release guidance from the root README to the contribution guide.

## 0.2.0 - 2026-09-12

### Added

- Added dependency-free repository validation and pull-request CI.
- Added `npx skills`, skills.sh, Codex plugin, and Claude Code plugin installation guides.
- Added Codex and Claude Code marketplace metadata and manifests.
- Added repository ownership metadata and a privacy policy.

### Changed

- Expanded contribution guidance for maintainer-controlled changes.
- Updated human-facing documentation for public distribution.

## 0.1.0 - 2026-09-11

### Added

- Added the `dev-docs` and `dev-rules` agent skills.
- Added root documentation, contribution guidance, security policy, and MIT license.
- Added skills.sh repository presentation metadata.
