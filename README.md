# HomeAssitant Custom Integration for Dyson

This custom integration is still under development.

This is a HA custom integration for dyson. It uses domain `dysonv2`. There are several main differences between this custom integration and the official dyson integration:

- It does not rely on dyson account. Which means once configured, the integration will no longer login to the Dyson cloud service so fast and more reliable start up process.

- Config flow and discovery is supported, so easier configuration.

- Based on a new library that is better structured so the code in the integration itself is simplified.

My goal is to make this integration official. However, at the current stage, I don't want to do the changes in core since there could be a lot of breaking changes. Therefore, I'll do be merge when everything seems stable.
