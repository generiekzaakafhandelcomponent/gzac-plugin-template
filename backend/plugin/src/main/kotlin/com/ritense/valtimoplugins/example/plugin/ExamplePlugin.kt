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

package com.ritense.valtimoplugins.example.plugin

import com.ritense.plugin.annotation.Plugin
import com.ritense.plugin.annotation.PluginAction
import com.ritense.plugin.annotation.PluginActionProperty
import com.ritense.processlink.domain.ActivityTypeWithEventName.SERVICE_TASK_START
import io.github.oshai.kotlinlogging.KotlinLogging
import org.operaton.bpm.engine.delegate.DelegateExecution

private val logger = KotlinLogging.logger {}

@Plugin(
    key = "example",
    title = "Example Plugin",
    description = "A minimal example plugin to use as a template for creating your own plugin"
)
open class ExamplePlugin {

    @PluginAction(
        key = "set-process-variable",
        title = "Set Process Variable",
        description = "Sets a process variable to a given value",
        activityTypes = [SERVICE_TASK_START]
    )
    open fun setProcessVariable(
        execution: DelegateExecution,
        @PluginActionProperty variableName: String,
        @PluginActionProperty variableValue: String,
    ) {
        logger.info { "Setting process variable '$variableName' to '$variableValue'" }
        execution.setVariable(variableName, variableValue)
    }
}
