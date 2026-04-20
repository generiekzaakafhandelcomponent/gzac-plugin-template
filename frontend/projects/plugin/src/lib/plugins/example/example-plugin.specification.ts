/*
 * Copyright 2026 Ritense BV, the Netherlands.
 *
 * Licensed under EUPL, Version 1.2 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {PluginSpecification} from "@valtimo/plugin";
import {ExampleConfigurationComponent} from "./components/example-configuration/example-configuration.component";
import {EXAMPLE_PLUGIN_LOGO_BASE64} from "./assets";
import {SetProcessVariableComponent} from "./components/set-process-variable/set-process-variable.component";

const examplePluginSpecification: PluginSpecification = {
  pluginId: "example",
  pluginConfigurationComponent: ExampleConfigurationComponent,
  pluginLogoBase64: EXAMPLE_PLUGIN_LOGO_BASE64,
  functionConfigurationComponents: {
    "set-process-variable": SetProcessVariableComponent,
  },
  pluginTranslations: {
    nl: {
      title: "Voorbeeld Plugin",
      "set-process-variable": "Procesvariabele instellen",
      description: "Een minimaal voorbeeld plugin om als sjabloon te gebruiken voor het maken van je eigen plugin.",
      configurationTitle: "Configuratienaam",
      configurationTitleTooltip:
        "De naam van de huidige plug-in configuratie. Onder deze naam kan de configuratie worden gevonden in de rest van de applicatie.",
      variableName: "Variabelenaam",
      variableNameTooltip: "De naam van de procesvariabele die wordt ingesteld.",
      variableValue: "Waarde",
      variableValueTooltip: "De waarde die wordt toegewezen aan de procesvariabele.",
    },
    en: {
      title: "Example Plugin",
      "set-process-variable": "Set Process Variable",
      description: "A minimal example plugin to use as a template for creating your own plugin.",
      configurationTitle: "Configuration Name",
      configurationTitleTooltip:
        "The name of the current plug-in configuration. The configuration can be found under this name in the rest of the application.",
      variableName: "Variable Name",
      variableNameTooltip: "The name of the process variable to set.",
      variableValue: "Value",
      variableValueTooltip: "The value to assign to the process variable.",
    },
  },
};

export {examplePluginSpecification};
