# From OpenAPI spec to plugin

Two halves: getting a usable API client out of the spec, and satisfying the
plugin contract that ties backend keys to frontend components.

## Where the spec lives

Commit it inside the plugin module so the build is self-contained:

```
backend/plugin/src/main/resources/openapi/<artifact>.yml
```

Keep the file the user handed over byte-for-byte if possible — a spec that is
also the vendor's published artifact is easier to re-sync later. If it needs
edits (missing `operationId`s, no `tags`), commit the original first, then the
edit, so the diff shows what you changed and why.

## Option A — generated client (default)

The template carries `openApiGeneratorPluginVersion` and `squareupMoshiVersion`
in `gradle.properties` but never wires the plugin up. Three edits, all required.

**1. `settings.gradle.kts`** — the version must be declared in
`pluginManagement` (this repo pins every plugin version there, see the comment
about gradle#1697):

```kotlin
pluginManagement {
    val openApiGeneratorPluginVersion: String by settings   // add to the existing vals

    plugins {
        id("org.openapi.generator") version openApiGeneratorPluginVersion   // add to the existing plugins
    }
}
```

**2. `backend/plugin/build.gradle.kts`** — `plugins {}` must be the first block
in the file, above `dockerCompose {}`:

```kotlin
plugins {
    id("org.openapi.generator")
}
```

and at the end:

```kotlin
val openApiOutput = layout.buildDirectory.dir("generated/openapi")

openApiGenerate {
    generatorName.set("kotlin")
    library.set("jvm-spring-restclient")
    inputSpec.set("$projectDir/src/main/resources/openapi/<artifact>.yml")
    outputDir.set(openApiOutput.map { it.asFile.path })
    packageName.set("com.ritense.valtimoplugins.<package>.openapi")
    configOptions.set(
        mapOf(
            "serializationLibrary" to "jackson",
            "useSpringBoot3" to "true",
        ),
    )
}

sourceSets.main {
    kotlin.srcDir(openApiOutput.map { it.dir("src/main/kotlin") })
}

// Both compile and lint read the generated tree, so both must wait for it.
// Without the ktlint dependency Gradle fails the build with an
// implicit-dependency validation error on runKtlintCheckOverMainSourceSet.
tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
    dependsOn(tasks.openApiGenerate)
}

tasks.withType<org.jlleitschuh.gradle.ktlint.tasks.BaseKtLintCheckTask> {
    dependsOn(tasks.openApiGenerate)
}
```

Use `Provider.map` for `outputDir`/`srcDir` as shown. The obvious
`openApiOutput.get().asFile.path` is a three-call chain on one line and
`ktlintKotlinScriptCheck` rejects it (`standard:chain-method-continuation`) —
the build script is linted too.

**3. `backend/.editorconfig`** — exempt the generated tree from ktlint:

```
# Generated OpenAPI client sources are not ours to format.
[**/build/generated/**.{kt,kts}]
ktlint = disabled
```

Do **not** try `ktlint { filter { exclude { … } } }` in the module build file.
The root `build.gradle.kts` applies the ktlint plugin from its `subprojects {}`
block *after* the Kotlin plugin, so the per-source-set lint tasks already exist
by the time a module-level `ktlint {}` block runs, and the filter is ignored.
The generated client trips ~120 violations (trailing commas, wildcard imports,
import order), so without this exemption `ktlintCheck` fails.

Verify with `./gradlew :backend:plugin:openApiGenerate` and inspect
`backend/plugin/build/generated/openapi/src/main/kotlin/…` before writing code
against it.

### What the generator produces

For `library = jvm-spring-restclient`:

- `apis/<Tag>Api.kt` — one class per spec `tags` entry; **operations with no tag
  all land in `DefaultApi`**. If the spec is untagged and has more than a handful
  of operations, add `tags` to it rather than living with one giant class.
- `models/*.kt` — data classes. **Every non-required property is nullable**, so
  actions and services must handle nulls explicitly rather than assuming a shape.
- `infrastructure/*.kt` — `ApiClient`, `Serializer`, request config.

The generated API class takes a Spring `RestClient`, which is exactly what the
scaffold's client already used:

```kotlin
class DefaultApi(client: RestClient) : ApiClient(client) {
    constructor(baseUrl: String) : this(/* … */)
    fun getPersoon(bsn: kotlin.String): Persoon
    fun getPersoonWithHttpInfo(bsn: kotlin.String): ResponseEntity<Persoon>
}
```

No new runtime dependencies are needed: it compiles against the module's
existing `compileOnly` spring-web and the Jackson that Valtimo already provides
at runtime. Do not add okhttp/moshi unless you deliberately switch `library`.

Keep the generated classes behind the plugin's own `*Client`/`*Service` pair —
the plugin class should never touch `openapi.apis.*` directly, so a spec
re-generation cannot ripple into the action signatures:

```kotlin
@SkipComponentScan
@Component
class BrpClient(
    private val restClient: RestClient = RestClient.create(),
) {
    fun getPersoon(baseUrl: String, bsn: String): Persoon =
        DefaultApi(RestClient.builder().baseUrl(baseUrl).build()).getPersoon(bsn)
}
```

## Option B — hand-written client

Better for a spec with one or two operations, or when the generated surface is
far larger than what the plugin exposes. Keep the scaffold's shape — the renamed
`*Client` (an `@SkipComponentScan @Component` around `RestClient`), the
`*Service` that maps responses to something process-friendly, and Kotlin data
classes for just the payload fields the plugin needs. Delete the sample's
`ApiResponse.kt`/`Timezone` and write the real DTOs; skip the codegen wiring and
the `.editorconfig` exemption entirely.

## The plugin contract

These names must line up exactly, or the plugin loads but its configuration
screens break at runtime. This is what the `plugin-pr-reviewer` agent checks.

| Thing | Backend | Frontend | Elsewhere |
|---|---|---|---|
| plugin id | `@Plugin(key = "<artifact>")` | `pluginId` in `*.specification.ts` | `pluginArtifactId`, metadata `name`, `@valtimo-plugins/<artifact>` |
| action key | `@PluginAction(key = "…")` | key in `functionConfigurationComponents` | `pluginActionDefinitionKey` in the example process-link, and the BPMN `serviceTask` id |
| config property | `@PluginProperty(key = "…")` | field in the `*PluginConfig` interface + `v-input name` | `properties` in the example `*.pluginconfig.json` |
| action property | `@PluginActionProperty` param name | field in the `*ActionConfig` interface + `v-input name` | `actionProperties` in the example process-link |
| translations | — | every key above, in **both** `nl` and `en` | — |

Backend details:

- `@PluginProperty(key = "…", secret = true)` for anything credential-shaped —
  tokens, client secrets, passwords. The scaffold's only property (`apiUrl`) is
  `secret = false`; a real API almost always adds at least one secret.
- Action methods take `execution: DelegateExecution` first when they need to
  write results back (`execution.setVariable(...)`), then
  `@PluginActionProperty` parameters.
- `activityTypes = [SERVICE_TASK_START]` for the usual fire-from-a-service-task
  action; other `ActivityTypeWithEventName` values exist for user-task and
  event-driven links.
- Register every new bean in the renamed `*AutoConfiguration` with
  `@ConditionalOnMissingBean`, matching the existing three.
- Keep `@SkipComponentScan` on clients/services — Valtimo scans differently and
  the annotation is what keeps plugin beans out of the host's component scan.

Frontend details:

- One action-configuration component per action, declared **and** exported in
  the plugin module, exported from `public_api.ts`, and mapped in
  `functionConfigurationComponents`.
- Components implement `FunctionConfigurationComponent` (actions) or
  `PluginConfigurationComponent` (plugin config), with the `save$`/`disabled$`/
  `prefillConfiguration$` inputs and `valid`/`configuration` outputs the
  scaffold already wires up — copy its subscription pattern rather than
  inventing one.
- `handleValid()` must check exactly the properties the backend marks required;
  a required backend property that is not validated produces a saveable but
  broken configuration.
- Every `v-input name="x"` must match a field `x` in the config interface and a
  translation key `x` in both languages.

Example app (`backend/app/src/main/resources/config/`): the sandbox app
autodeploys `plugin/<artifact>.pluginconfig.json`, the case's `process-link`
JSON and `bpmn/example-process.bpmn`. Keep one action wired end-to-end there so
`./gradlew :backend:app:bootRun` still demonstrates something real. The
`pluginConfigurationId` UUID in the process-link must match the `id` in the
pluginconfig JSON.