rootProject.name = "quantum-trading-platform"

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

include("quantum-platform-core:quantum-shared-kernel")
include("quantum-platform-core:quantum-trading-command")
include("quantum-platform-core:quantum-trading-query")

include("quantum-web:quantum-web-api")
include("quantum-web:quantum-web-client")

