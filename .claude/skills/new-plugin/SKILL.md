---
name: new-plugin
description: Turn this gzac-plugin-template checkout into a real GZAC/Valtimo plugin — rename the sample scaffold (artifact id, project name, version) and implement the plugin, actions and Angular config forms against an OpenAPI spec. Use when asked to "create a new plugin", "generate a plugin from the template", "scaffold a plugin", or when handed an openapi.yml/openapi.yaml to build a plugin from.
---

# Generate a plugin from this template

Two phases. Phase 1 is a deterministic rename done by a script. Phase 2 is the
part that needs judgement: turning the OpenAPI spec into a plugin with actions
and matching frontend forms.

Never skip Phase 1's script and rename by hand — `sample`/`Sample`/`sampleplugin`/
`SAMPLE_PLUGIN`/`gzac-plugin-template` appear across ~50 files and four casings,
and a missed one produces a plugin that builds but does not load.

## Phase 0 — collect inputs

Ask the user with **one** AskUserQuestion call (all four in a single call), unless
they already stated the answer:

1. **Artifact id** — kebab-case, becomes the Maven artifactId, the npm package
   name (`@valtimo-plugins/<artifact>`), the `@Plugin(key=…)` and the frontend
   `pluginId`. Convention is a `-plugin` suffix (`brp-plugin`, `spotler-plugin`).
2. **Project name** — kebab-case, becomes `rootProject.name`, `projectName` in
   `gradle.properties`, the Angular application project key and the repo name in
   the `scm` block. Usually the same as the artifact id; offer that as default.
3. **Initial version** — `MAJOR.MINOR.PATCH`. Offer `0.0.1` and `0.1.0`.
4. **Client strategy** — how the backend talks to the API:
   - *generated* (default): wire the `org.openapi.generator` Gradle plugin and
     generate a Kotlin client from the committed spec.
   - *hand-written*: a `RestClient` client + Kotlin data classes written from the
     spec, following the scaffold's existing `*Client`/`*Service` shape. Prefer
     this for a spec with only a couple of operations.

Also confirm the **path to the OpenAPI spec** and the **plugin title** (defaults
to the artifact id title-cased, e.g. `Brp Plugin`).

Before doing anything: `git status`. The rename rewrites the working tree in
place, so require a clean tree (or an explicit go-ahead) and note the current
branch — offer to branch first if on `main`.

## Phase 1 — rename the scaffold

```bash
python3 .claude/skills/new-plugin/scripts/rename_template.py \
  --artifact <artifact> --project <project> --version <version> [--title "<Title>"]
```

Add `--dry-run` first if the user wants to preview. The script renames paths
(`git mv`), rewrites contents in every text file, sets the version in the four
places that carry it, and then greps for leftovers — it prints
`no leftover template names` when the rename is complete. If it warns about
leftovers, fix those files before continuing.

What it does **not** do, and you must: the sample's *prose and API semantics*.
After it runs, `Sample Plugin`-flavoured text survives as `<Base> plugin`
("This is a brp plugin demonstrating an API call action") and the sample's
Time-API shape survives as real code (`ApiResponse`, `Timezone`, `fetchTimeAPI`,
`apiUrl`, action key `time-api-<base>-action`). Phase 2 replaces all of it.

See `references/rename-inventory.md` for the full file-by-file map of what
carries which name — use it to verify, or to redo a rename by hand if the script
cannot run.

## Phase 2 — implement against the OpenAPI spec

Read `references/openapi-to-plugin.md` before writing code. It covers:

- where the spec lives and the three edits that wire up `org.openapi.generator`
  — the `settings.gradle.kts` `pluginManagement` entry the template is missing,
  the module `build.gradle.kts` block, and the `backend/.editorconfig` ktlint
  exemption without which `ktlintCheck` fails on ~120 generated-code violations.
  Copy that wiring verbatim; each piece of it is there because the build fails
  without it.
- the hand-written `RestClient` alternative,
- the contract every plugin must satisfy: which keys and property names have to
  match between `@Plugin`/`@PluginAction`, the frontend specification,
  `models/config.ts`, the translations and the example app's autodeploy config.

Order of work:

1. Commit the spec, then choose the operations to expose. List the spec's
   operations and ask which should become plugin actions (default: all) — a
   plugin action per operation is the norm, but a spec with dozens of operations
   should be narrowed.
2. Backend: config properties on the plugin class (`@PluginProperty`, with
   `secret = true` for tokens/passwords), client + service, one
   `@PluginAction` per chosen operation.
3. Frontend: one action-configuration component per action, `models/config.ts`
   interfaces matching the backend property names exactly, `nl` **and** `en`
   translations for every key.
4. Example app: update `backend/app/src/main/resources/config/plugin/<artifact>.pluginconfig.json`,
   the `process-link` JSON and the BPMN service task id so the sandbox app still
   starts and demonstrates one action.
5. Docs: rewrite `documentation/plugin.md` (overview, config table, one section
   per action), `documentation/getting-started.md`, `README.md` (including the
   contact placeholder) and the `documentation/release-notes.md` entry.

## Phase 3 — verify

Run and report actual output; do not claim success without it:

```bash
./gradlew :backend:plugin:compileKotlin :backend:plugin:ktlintCheck
cd frontend && npm install && npm run lint && npm run build --workspace=@valtimo-plugins/<artifact>
```

The frontend commands mirror what `.github/workflows/pr-checks.yaml` runs, plus
the library build. `npm install` here is slow (full Valtimo/Angular tree) — say
so before starting it rather than appearing to hang.

`./gradlew :backend:plugin:test` needs Docker (it starts a postgres via
docker-compose) — run it if Docker is available, otherwise say it was skipped.

Then check the cross-cutting consistency by hand:

- `@Plugin(key)` == frontend `pluginId` == `valtimo-configurator-metadata.json`
  `name` == `pluginArtifactId` == npm package suffix.
- every `@PluginAction(key)` has an entry in `functionConfigurationComponents`
  and a translation in both `nl` and `en`.
- every `@PluginActionProperty` parameter name appears in the action's
  `models/config.ts` interface and as a `v-input name=…` in its template.
- `valtimo-configurator-metadata.json` `spec`/`module` match the exported
  specification constant and module class.

This repo also has a `plugin-pr-reviewer` agent that checks exactly these
invariants — offer to run it as a final review, and let the user decide.