# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- `uv.lock` now records the project version, so a release commit no longer breaks `uv sync --locked` in CI and in the
  Docker build; `.bumpversion.toml` keeps the lock in step with `pyproject.toml`

### Security
- GitPython updated to 3.1.62, clearing six advisories including a `check_unsafe_options` guard bypass that allowed
  command execution via short-option smuggling (GHSA-wvpp-8hx9-p66j)

## [0.5.0] - 2026-09-07
### Added
- Push retry with exponential backoff: up to 3 attempts with pull-rebase on rejected updates
- End-to-end tests with real git operations against local bare repositories

### Changed
- Switched packaging and dependency management from Poetry to uv (`uv.lock` replaces `poetry.lock`)
- `pyproject.toml` now uses PEP 621 metadata with the `uv_build` backend
- Dependencies updated, including the majors environs 15, pytest 9, pytest-cov 7 and mypy 2
- Runtime moved to Python 3.14 on Debian 13 (trixie); `requires-python` is now `>=3.14`
- Local automation moved from `Makefile` to `Taskfile.yml`
- Version bumping now uses `bump-my-version` with `.bumpversion.toml`
- pre-commit hooks updated and now enforced in CI, with `check-yaml` and `check-toml` added; pre-commit is a
  locked dev dependency, and CI runs tools with `uv run --no-sync` so they come from `uv.lock` rather than a
  fresh resolution
- Removed the Renovate configuration; dependency, base image, action SHA and pre-commit `rev` updates are
  now done by hand
- `description` is now optional in the Chart model, matching the Helm specification
- Replace `sys.exit()` flow control with domain exceptions (`NoUpdateNeededError`, `ChartValidationError`)
- Raise `ValueError` instead of `IndexError` when README table markers are missing
- Capture and log helm-docs stderr on failure instead of silently discarding it
- Pin all GitHub Actions to commit SHAs for supply-chain security
- CI workflow renamed to Quality Assurance (`qa.yml`)
- Rebase on push-retry no longer auto-resolves conflicts with the `ours` strategy; conflicts now propagate as errors
- Chart discovery (`get_charts_list`) now searches within `charts_path` instead of the full clone root
- `importValues` in Dependency model now accepts both string and dict entries per the Helm spec
- README now explains the update flow with a diagram and carries CI, coverage and Python version badges

### Fixed
- Rejected pushes are now detected: GitPython reports them through `PushInfo` flags rather than by raising, so a
  push lost to a concurrent commit was previously logged as a success and the chart update silently discarded
- Updating a chart no longer rewrites the whole Chart.yaml from the model: comments, key order and fields outside
  the Chart model (`home`, `deprecated`, custom keys) were being dropped on every run
- `appVersion` is written as a quoted string, so a value such as `1.10` is no longer read back as the number `1.1`
- Chart.yaml writes preserve the file's quoting, line width, line endings and leading `---` marker, so a version
  bump no longer produces a whole-file diff — and no longer strips a document-start marker that yamllint requires.
  One case remains unmatched: in a chart that contains block sequences, nested mapping indentation is re-emitted
  at ruamel's default of two spaces
- Malformed YAML and non-mapping Chart.yaml documents now raise `ChartValidationError` instead of untyped exceptions
- Credential sanitization in re-raised exceptions now uses `from None` to prevent leakage via implicit exception chaining
- Docker image now installs from `uv.lock` for reproducible builds
- CRLF line endings in README files are now properly preserved during table replacement

### Security
- helm-docs is fetched with `ADD --checksum=sha256:...` against a digest pinned in the Dockerfile, rather than
  with `curl` verified against the upstream `checksums.txt`. The pin cannot be swapped by whoever can replace
  the archive, and `curl` is no longer installed in the image at all. The digest must be updated alongside
  `HELM_DOCS_VERSION`
- GitPython (3.1.57) and pytest (9.1.1) updated to clear published security advisories

## [0.4.3] - 2025-04-22
### Fixed
- Issue in poetry.lock file

## [0.4.2] - 2025-04-22
### Changed
- Dependency updates to resolve broken builds

## [0.4.1] - 2024-02-27
### Fixes
- Formatting for multi line values

## [0.4.0] - 2024-02-13
### Added
- Support for basic commit issue resolution
### Changed
- Bumped project dependencies
### Fixed
- Chart.yaml annotations are properly formatted now

## [0.3.4] - 2024-02-12
### Fixed
- Missed argument in actions.yml

## [0.3.3] - 2024-02-12
### Added
- Support for overriding clone path

## [0.3.2] - 2023-08-27
### Added
- Support for keywords in Chart.yaml

## [0.3.1] - 2023-08-26
### Changed
- Bumped project dependencies

## [0.3.0] - 2023-06-13
### Added
- Support for updating chart annotation with the updated appVersion
### Changed
- Replace `exit` with `sys.exit`

## [0.2.11] - 2022-11-07
### Changed
- Changed default value for `update_readme` to `false`

## [0.2.10] - 2022-10-19
### Changed
- Removed [skip ci] from commit message

## [0.2.9] - 2022-10-18
### Changed
- The generated table is now sorted by name

## [0.2.8] - 2022-10-15
### Changed
- Project build approach
- Return default source image in Dockerfile
- Append [skip ci] to the commit message

## [0.2.7] - 2022-09-30
### Changed
- Decreased build time by setting custom source image for Dockerfile

## [0.2.6] - 2022-09-23
### Changed
- Simplified Dockerfile

## [0.2.5] - 2022-09-18
### Changed
- Generated table has "type" column now

## [0.2.4] - 2022-08-27
### Changed
- Makes it possible to set committer user.name and user.email
- Makes it possible to set charts path
- Removed redundant default values from config.py

## [0.2.3] - 2022-08-18
### Changed
- print to logging
- os.system to subprocess

### Fixed
- Raise correct error in models validation

## [0.2.2] - 2022-08-14
### Changed
- Helm Class is using Chart model now

## [0.2.1] - 2022-08-13
### Fixed
- Default values for optional parameters

## [0.2.0] - 2022-08-13
### Added
- Support for generating table of the existing charts in the README.md file.
### Changed
- Shell calls were changed to GitPython
- Approach for collecting environment variables
- Make helm docs generation optional

## [0.1.2] - 2022-08-12
### Fixed
- Add git and helm-docs to the image
### Changed
- CMD to ENTRYPOINT

## [0.1.1] - 2022-08-12
### Fixed
- Remove "--chown=app:app" from Dockerfile

## [0.1.0] - 2022-08-12
### Added
- Initial version
