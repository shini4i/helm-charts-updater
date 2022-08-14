# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
