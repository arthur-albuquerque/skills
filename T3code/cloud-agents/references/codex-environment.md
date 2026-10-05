# Set up current Codex Cloud

For an existing published environment, use the terminal workflow in [codex.md](codex.md): register its config ID, dispatch a fresh validation task, and inspect its result. Environment creation/publication is separate from task dispatch; the adapter currently implements the latter. The configuration-panel procedure below applies when browser setup is permitted. For a terminal-only setup request, use a verified current environment-config API/connector and its actual schema instead of invoking that panel.

1. Inspect the repository's manifests, lockfiles, `AGENTS.md`, and CI. Identify its runtime, installation, startup, and validation commands.
2. Open ChatGPT **Settings > Codex Cloud > Environments > Create environment** at https://chatgpt.com/settings/codex-cloud. Select the GitHub repository and **Get started**. Supply missing login/access through the user when required. Use the current publish-based workflow.
3. In the setup conversation, specify the toolchain, isolated repository scope, startup/readiness criteria, and required checks. Keep repository files unchanged while configuring the environment; the reusable start skill should allow future tasks to edit their assigned files.
4. Inspect the configuration panel. Set a clear name, the actual repository, an install script, and a concise start skill. Group prerequisites, startup, and checks; remove historical failures once resolved. Save a local copy of the tested configuration under `~/.codex/cloud-agents/environments/<slug>/`.
5. Configure actual network needs in the panel, save changes, and retry failed setup commands. A domain allowlist does not supply credentials or root access. Inspect failed download URLs and redirect domains before changing policy. Current environment-variable/network-secret controls differ from legacy setup-only secrets; follow the current UI.
6. Run required checks in the setup workspace. Record their commands and full results, browser/service readiness, and any repository changes. Resolve environment blockers before publishing; distinguish application test failures from missing dependencies.
7. Save the tested configuration and **Publish**. Confirm **Environment published**, then run a small task from the published environment to verify its snapshot, startup, and result. Store the exact config ID, settings URL, and task URL. Probe CLI compatibility only against this published environment; document what actually works.

Done when the current environment is published for the correct repository, runtime/startup checks work in a new cloud task, required validations are recorded, and available dispatch/monitoring transports are documented. If external access prevents completion, save a concrete draft and state the exact unresolved requirement.

## trips_platform general-purpose setup

This project-specific example describes the environment used to exercise the adapter; register your own published environment for other repositories.
Repository: `arthur-albuquerque/viagem-trip-platform`.
Environment: `viagem-default`.

Python >=3.12, `uv.lock`, a Git-pinned flight dependency, and Playwright Chromium are the inputs. Match CI's locked sync and browser installation, adapting privileged system-library installation to the current container's permissions. Validation is `uv run pytest`; `uv run pytest -m 'not browser'` narrows diagnosis when Chromium is unavailable. Tests use recordings and need no live API keys. Start the app with its documented fake-source workflow for credential-free readiness.

The local environment record is `~/.codex/cloud-agents/environments/viagem-default/README.md`; read it for the current config ID, scripts, verified results, network domains, and CLI compatibility. R/Quarto/Stan is a separate setup when requested.

Reference: [current cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments).
