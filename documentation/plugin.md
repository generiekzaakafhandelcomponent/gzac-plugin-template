# Plugin Documentation

<!-- Use this page to document your plugin. Below is a suggested structure. -->

## Overview

Describe what your plugin does and what problem it solves.

## Dependencies

### Backend

```kotlin
dependencies {
    implementation("com.ritense.valtimoplugins:example:8.1.0")
}
```

### Frontend

```json
{
  "dependencies": {
    "@valtimo-plugins/example": "8.1.0"
  }
}
```

In your `app.module.ts`:

```typescript
import {
    ExamplePluginModule, examplePluginSpecification,
} from '@valtimo-plugins/example';

@NgModule({
    imports: [
        ExamplePluginModule,
    ],
    providers: [
        {
            provide: PLUGIN_TOKEN,
            useValue: [
                examplePluginSpecification,
            ]
        }
    ]
})
```

## Configuration

List the plugin configuration properties and how to set them.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
|          |      |          |             |

## Actions

### Action Name

Describe what this action does, when it runs, and what parameters it accepts.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
|           |      |          |             |

## Usage

Explain how to use the plugin in a process, with examples if applicable.
