# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
