# resource-resolution Specification

## Purpose

Defines how the application locates its two kinds of files: read-only resources that ship inside the
application, and writable state that lives on the user's disk. This is where running frozen differs
from running from source.

## Requirements

### Requirement: Bundled frontend is found when frozen

The application MUST locate the built frontend relative to the running application, not relative to
the source file's position on a developer machine. When frozen, the location MUST be resolved from the
temporary unpack directory of the bundle.

#### Scenario: Frozen application serves the UI

- GIVEN the packaged executable, with the built frontend inside the bundle
- WHEN a browser requests `/`
- THEN the response MUST be the built `index.html`
- AND a request for a client route such as `/observaciones/123` MUST return `index.html` with 200

#### Scenario: Development is unaffected

- GIVEN the repository, with `.venv` created by hand and no frozen bundle
- WHEN the backend runs from source with `frontend/dist` built
- THEN it MUST serve that same `frontend/dist`

#### Scenario: No built frontend available

- GIVEN no built frontend can be found
- WHEN the backend starts
- THEN it MUST start anyway and MUST report that only the API is available

### Requirement: Writable paths are resolved before settings are read

The application MUST determine the database and image locations before settings are instantiated, so
that no component depends on the process's current working directory.

#### Scenario: Launched from a different working directory

- GIVEN the packaged executable and a working directory that is not the application folder
- WHEN the launcher starts the server
- THEN the database and images MUST resolve next to the executable
- AND no file MUST be written into the working directory

#### Scenario: Running from source keeps today's behaviour

- GIVEN the repository and the command used by `arrancar.bat`
- WHEN the backend runs from source
- THEN the database MUST stay at `backend/riguel.db`
- AND images MUST stay at `backend/data/imagenes`

### Requirement: The images directory exists before the application is imported

The application MUST NOT fail to start because the images directory is missing. The directory has to
exist by the time the application module is imported.

#### Scenario: Images directory absent on a cold start

- GIVEN a fresh data directory with no `imagenes` subdirectory
- WHEN the launcher starts the server
- THEN startup MUST succeed
- AND the default logo MUST be downloadable at the images URL

#### Scenario: Static mount cannot crash the process

- GIVEN the images directory does not exist at the moment the application module is imported
- WHEN the launcher starts the server
- THEN the process MUST NOT die

### Requirement: Reserved API paths keep returning 404

Making the frontend resolution frozen-aware MUST NOT change which paths fall through to the client
application.

#### Scenario: Unknown API route

- GIVEN the packaged application
- WHEN `/api/v1/noexiste` is requested
- THEN the response MUST be 404
- AND it MUST NOT be the client application's `index.html`

#### Scenario: Known API route

- GIVEN the packaged application
- WHEN `/api/v1/observatorio` is requested
- THEN the response MUST be the observatory JSON
