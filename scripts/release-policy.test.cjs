const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { createRequire } = require('node:module');
const { resolve } = require('node:path');
const { test } = require('node:test');

const root = resolve(__dirname, '..');
assert.ok(process.env.RELEASE_POLICY_DEPS, 'Set RELEASE_POLICY_DEPS to the test dependency directory');
const load = createRequire(resolve(process.env.RELEASE_POLICY_DEPS, 'package.json'));
const { Manifest, setLogger } = load('release-please');
const { parseConventionalCommits } = load('release-please/build/src/commit');
const { TagName } = load('release-please/build/src/util/tag-name');
const read = path => readFileSync(resolve(root, path), 'utf8');
setLogger({ debug() {}, info() {}, warn() {}, error() {} });

// Only repository reads are substituted; parsing, versioning, notes and updaters
// come from the same Release Please engine used by the release action.
const github = {
  repository: { owner: 'kovaa-dev', repo: 'skills' },
  async getFileJson(path) { return JSON.parse(read(path)); },
};
const manifest = Manifest.fromManifest(github, 'main');

async function candidate(messages) {
  const release = await manifest;
  const strategy = (await release.getStrategiesByPath())['.'];
  const version = release.releasedVersions['.'];
  return strategy.buildReleasePullRequest(
    parseConventionalCommits(messages.map((message, index) => ({
      message, sha: String(index + 1).padStart(40, '0'), files: [],
    }))),
    { tag: new TagName(version), sha: '0'.repeat(40) },
  );
}

for (const [type, level] of [
  ['docs', 'patch'], ['fix', 'patch'], ['perf', 'patch'],
  ['revert', 'patch'], ['feat', 'minor'], ['feature', 'minor'], ['docs!', 'major'],
]) {
  test(`${type} creates a ${level} release`, async () => {
    const previous = (await manifest).releasedVersions['.'];
    const expected = {
      patch: `${previous.major}.${previous.minor}.${previous.patch + 1}`,
      minor: `${previous.major}.${previous.minor + 1}.0`,
      major: `${previous.major + 1}.0.0`,
    }[level];
    const result = await candidate([`${type}: update skill instructions`]);
    assert.ok(result, 'expected a release PR candidate');
    assert.equal(result.version.toString(), expected);
  });
}

for (const type of ['chore', 'ci', 'test', 'build', 'style', 'refactor']) {
  test(`${type} alone does not create a release`, async () => {
    assert.equal(await candidate([`${type}: maintain repository`]), undefined);
  });
}

test('docs-only release includes notes and synchronized managed versions', async () => {
  const result = await candidate(['docs: clarify measurement criteria']);
  assert.ok(result, 'docs-only changes must produce a release PR');
  const version = result.version.toString();
  const updates = new Map(result.updates.map(update => [update.path, update]));
  const changelog = updates.get('CHANGELOG.md').updater.updateContent(read('CHANGELOG.md'));
  assert.match(changelog, /### Documentation/);
  assert.match(changelog, /clarify measurement criteria/);
  for (const path of ['.codex-plugin/plugin.json', '.claude-plugin/plugin.json']) {
    const content = updates.get(path).updater.updateContent(read(path));
    assert.equal(JSON.parse(content).version, version);
  }
  const marketplace = updates.get('.claude-plugin/marketplace.json');
  assert.equal(JSON.parse(marketplace.updater.updateContent(read(marketplace.path))).plugins[0].version, version);
  for (const path of ['README.md', 'skills/dev-docs/README.md', 'skills/dev-rules/README.md']) {
    const content = updates.get(path).updater.updateContent(read(path));
    assert.ok(content.includes(`v${version}`), `${path} must publish the new version`);
  }
});

test('feature bump wins over accumulated docs changes', async () => {
  const previous = (await manifest).releasedVersions['.'];
  const result = await candidate(['docs: clarify instructions', 'feat: add a new skill workflow']);
  assert.equal(result.version.toString(), `${previous.major}.${previous.minor + 1}.0`);
});

test('breaking footer on a maintenance commit creates a major release', async () => {
  const previous = (await manifest).releasedVersions['.'];
  const result = await candidate(['refactor: reorganize skills\n\nBREAKING CHANGE: remove the old skill entry point']);
  assert.ok(result);
  assert.equal(result.version.toString(), `${previous.major + 1}.0.0`);
});
