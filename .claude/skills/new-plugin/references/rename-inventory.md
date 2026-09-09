# What carries a template name

Reference for verifying `rename_template.py`, or for renaming by hand if it
cannot run. Generated from the template at version 0.0.1 — if the template has
moved on, re-derive with:

```bash
git ls-files | grep -v '^\.idea' | xargs grep -ril 'sample\|gzac-plugin-template'
```

## The five spellings

| In the template | Becomes | Example |
|---|---|---|
| `sample-plugin` | artifact id | `brp-plugin` |
| `sampleplugin` | package segment (artifact minus dashes) | `brpplugin` |
| `Sample` | PascalCase base (artifact minus `-plugin` suffix) | `Brp` |
| `sample` before an uppercase letter | camelCase base | `sampleClient` → `brpClient` |
| `sample` elsewhere | kebab-case base | `sample-action-configuration` → `brp-action-configuration` |
| `SAMPLE_PLUGIN` | UPPER_SNAKE artifact | `BRP_PLUGIN` |
| `Sample Plugin` | plugin title | `BRP Plugin` |
| `gzac-plugin-template` | project name | `brp-plugin` |

Multi-word artifacts are why the camelCase case is separate: for
`kvk-handelsregister-plugin`, `sampleClient` must become
`kvkHandelsregisterClient`, not `kvk-handelsregisterClient`.

Never substitute inside a line containing `;base64,` — the logo constant's value
is base64 and a chance `sample`-like substring there would corrupt the image.

## Paths that get renamed

```
backend/plugin/src/main/kotlin/com/ritense/valtimoplugins/sampleplugin/     -> <package>/
    autoconfiguration/SampleAutoConfiguration.kt                            -> <Pascal>AutoConfiguration.kt
    client/SampleClient.kt, client/SampleService.kt                          -> <Pascal>Client.kt, <Pascal>Service.kt
    plugin/SamplePlugin.kt, plugin/SamplePluginFactory.kt                    -> <Pascal>Plugin.kt, <Pascal>PluginFactory.kt
backend/plugin/src/test/kotlin/com/ritense/valtimoplugins/sampleplugin/     -> <package>/
frontend/projects/plugin/src/lib/plugins/sample-plugin/                     -> <artifact>/
    sample-plugin-module.ts, sample-plugin.specification.ts                  -> <artifact>-module.ts, <artifact>.specification.ts
    assets/sample-plugin-logo.ts                                             -> assets/<artifact>-logo.ts
    components/sample-plugin-configuration/*.component.{ts,html}             -> components/<artifact>-configuration/
    components/sample-action-configuration/*.component.{ts,html}             -> components/<base>-action-configuration/
```

`client/ApiResponse.kt` keeps its name but holds the sample's `Timezone` DTO —
it is Phase 2's job to replace or delete it.

## Files whose contents carry the plugin name

Root and build:

- `valtimo-configurator-metadata.json` — `name`, `backend[].import`, `frontend.import`, `codeAdditions[].spec`/`.module`
- `settings.gradle.kts` — `rootProject.name`
- `gradle.properties` — `projectName`, `projectVersion`
- `build.gradle.kts` — `dockerCompose.projectNamePrefix`
- `gradle/publishing.gradle` — `scm` connection/developerConnection/url (**repo URL: check the GitHub org by hand, the script only swaps the repo name**)
- `README.md`, `documentation/{plugin,getting-started,release-notes}.md`
- `.env.properties.example` — `SAMPLE_PLUGIN_API_URL`
- `docker-resources/docker-compose-base-test.yml` — `POSTGRES_DB`, and the port-registry comment block

Backend plugin module:

- `backend/plugin/plugin.properties` — `pluginArtifactId`, `pluginVersion` (`pluginGroupId` stays `com.ritense.valtimoplugins`)
- `backend/plugin/build.gradle.kts` — `dockerCompose.setProjectName`
- `backend/plugin/gradle/publishing.gradle` — pom `name`, `description`
- `backend/plugin/docker-compose-override.yml` — `POSTGRES_DB`, port `54342`
- `backend/plugin/src/test/resources/config/application.yml` — jdbc url (db name + port)
- `backend/plugin/src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` — FQN of the autoconfiguration class
- all `.kt` files — package, imports, class names, `@Plugin(key)`, `@PluginAction(key)`

The db port `54342` is the template's slot in a shared registry that only
matters inside the monorepo this template was extracted from. A standalone
plugin repo can keep it; only change it if this plugin's tests run alongside
others on one host.

Example app:

- `backend/app/src/main/resources/config/application.yml` — `spring.application.name`
- `backend/app/src/main/resources/config/plugin/example.pluginconfig.json` — `pluginDefinitionKey`, `properties`
- `backend/app/src/main/resources/config/case/example/1-0-0/`
  - `process-link/example-process.process-link.json` — `pluginDefinitionKey`, `pluginActionDefinitionKey`, `activityId`, `actionProperties`
  - `bpmn/example-process.bpmn` — service task id (×2 flows + ×1 shape), task name
  - `case/widget-tab/example.case-widget-tab.json` — widget title
  - `document/definition/example.schema.document-definition.json` — property description
  - `form/start-form-example.form.json` — help text

Frontend:

- `frontend/package.json` — `name`
- `frontend/angular.json` — application project key, `outputPath`, two `buildTarget`s, library project key
- `frontend/tsconfig.json` — `paths` mapping for `@valtimo-plugins/<artifact>`
- `frontend/projects/plugin/package.json` — `name`, `version`, both `scripts`
- `frontend/projects/plugin/README.md`
- `frontend/projects/plugin/src/public_api.ts` — five export paths
- `frontend/src/app/app.module.ts` — import statement, `imports:` entry, `PLUGINS_TOKEN` entry
- the library sources under `src/lib/plugins/<artifact>/` — module, specification (`pluginId`, logo const, `functionConfigurationComponents`, translations), components (class names, selectors, `templateUrl`), `models/config.ts`, `assets/index.ts`

## Version lives in four places

`gradle.properties` (`projectVersion`), `backend/plugin/plugin.properties`
(`pluginVersion`), `frontend/projects/plugin/package.json` (`version`), and the
dependency snippets in `documentation/plugin.md` — plus the
`documentation/release-notes.md` heading. The script keeps all five in step;
keep them in step by hand on later releases too.