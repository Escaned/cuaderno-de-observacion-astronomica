# distribution Specification

## Purpose

Defines how the deliverable for end users is produced and, above all, how it is proven to work before
it is handed over.

## Requirements

### Requirement: The current script distribution keeps working

Producing the executable MUST NOT change what `empaquetar.ps1` does by default. The script zip keeps
being built and verified exactly as it is today.

#### Scenario: Default packaging run

- GIVEN a clean checkout with npm available and the port free
- WHEN `empaquetar.ps1` runs with no switches
- THEN it MUST produce the script zip
- AND it MUST install and boot that zip from scratch in a temporary folder
- AND it MUST fail the run if the application does not respond

#### Scenario: Port already in use

- GIVEN a process is listening on the packaging port
- WHEN `empaquetar.ps1` runs
- THEN it MUST refuse to start and say which port is busy

### Requirement: Building the executable is opt-in

Building the executable MUST be requested explicitly, so a routine packaging run never depends on the
frozen build.

#### Scenario: Executable build requested

- GIVEN the PyInstaller toolchain is installed
- WHEN packaging is run with the executable switch
- THEN an executable folder MUST be produced next to the script zip
- AND the toolchain version MUST be pinned, so the build is reproducible

#### Scenario: Toolchain missing

- GIVEN PyInstaller is not installed
- WHEN packaging is run with the executable switch
- THEN it MUST stop with a clear message naming what to install
- AND it MUST NOT leave a half-built folder behind

### Requirement: The executable is verified by running it

A built executable MUST NOT be considered valid because the build finished. The packaged artifact MUST
be exercised from scratch, without Python available to it, before it is offered for download.

#### Scenario: Packaged application serves the UI and the API

- GIVEN the freshly built executable folder
- WHEN it is launched in a clean location
- THEN `/health` MUST answer 200
- AND the UI, a client route, the observatory API and the default logo MUST all respond 200
- AND an unknown API route MUST still answer 404

#### Scenario: PDF export from the packaged application

- GIVEN the packaged application running
- WHEN a report is exported
- THEN the response MUST be a PDF
- AND the export MUST NOT fail on a missing font or a missing data file

#### Scenario: Logo upload from the packaged application

- GIVEN the packaged application running
- WHEN a logo is uploaded
- THEN it MUST be stored under the data directory
- AND it MUST still be served after a restart

#### Scenario: A failure fails the build

- GIVEN any of the checks above fails
- WHEN packaging concludes
- THEN the run MUST end in a non-zero exit and MUST NOT announce a valid package

### Requirement: No development state ships

The packaged artifact MUST NOT contain development dependencies, local databases, user photos or build
caches.

#### Scenario: Clean artifact

- GIVEN a repository with `node_modules`, `.venv`, a `riguel.db` and uploaded photos
- WHEN the artifact is built
- THEN it MUST contain none of them
- AND it MUST contain the compiled frontend and the default logo

### Requirement: End user documentation matches the artifact

The installation guide MUST describe the executable as the way to install, MUST state plainly what to
do about the Windows protection warning, and MUST explain how to carry data over from a script install.

#### Scenario: A non-technical user reads the guide

- GIVEN a user with no Python installed
- WHEN they follow the guide
- THEN nothing in it MUST require Python, pip, a terminal command or editing a file
- AND it MUST tell them to keep the folder together and not to move the executable out of it

#### Scenario: Data migration is documented

- GIVEN a user who already had a script install with observations
- WHEN they read the guide
- THEN it MUST explain how to bring those observations over
