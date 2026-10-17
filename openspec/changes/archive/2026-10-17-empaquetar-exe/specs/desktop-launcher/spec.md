# desktop-launcher Specification

## Purpose

The packaged entry point: where writable state lives, how the database is bootstrapped, and how it behaves
towards the user.

## Requirements

### Requirement: Writable state lives outside the bundle

The launcher MUST keep the database and uploaded images in `data/`, next to the executable, and MUST NOT
write inside the bundle.

#### Scenario: First run creates the data directory

- GIVEN a folder with the executable and no `data` directory
- WHEN the user launches it
- THEN `data/riguel.db` and `data/imagenes/` MUST exist before the server starts

#### Scenario: State survives an upgrade

- GIVEN `data/riguel.db` holds 4 observations
- WHEN the user replaces the folder with a newer build
- THEN the 4 observations MUST still be listed

### Requirement: The server listens on loopback only

The launcher MUST bind the server to loopback, so the observations stay off the local network.

#### Scenario: Not reachable from another machine

- GIVEN the packaged application running
- WHEN another machine on the same network requests its port
- THEN the connection MUST be refused

### Requirement: First-run bootstrap seeds the database

The launcher MUST bring the database to the current schema with the project migrations, so their seed data is
present. Creating tables alone is NOT sufficient.

#### Scenario: Fresh install is seeded

- GIVEN no database exists
- WHEN the launcher runs
- THEN the observatory "Riguel" MUST exist
- AND the 6 standard filters (L, R, G, B, Ha, OIII) MUST exist

#### Scenario: Existing database is only updated

- GIVEN a database at the current revision holding 3 observations
- WHEN the launcher runs
- THEN the 3 observations MUST be unchanged
- AND no seed row MUST be duplicated

#### Scenario: Migration failure stops the launcher

- GIVEN the database file is corrupt or locked
- WHEN the launcher runs
- THEN it MUST NOT start the server
- AND it MUST report what failed and where the database is

### Requirement: Adoption of an existing script install

The launcher MUST adopt the database of an existing script install instead of starting empty, and MUST NOT
destroy it.

#### Scenario: Legacy database found

- GIVEN `backend/riguel.db` sits next to the executable and `data/riguel.db` does not
- WHEN the launcher runs
- THEN it MUST copy it to `data/riguel.db`
- AND it MUST say so in plain language
- AND the original file MUST remain in place

#### Scenario: Both databases exist

- GIVEN both files exist
- WHEN the launcher runs
- THEN it MUST use `data/riguel.db` and MUST NOT overwrite it

### Requirement: Port handling

The launcher MUST NOT fail when the port already serves the application, and MUST NOT move ports silently.

#### Scenario: The application is already running

- GIVEN another instance is listening on the port
- WHEN the user launches the executable again
- THEN the browser MUST open pointing at the running instance
- AND no second server MUST be started

#### Scenario: The port is taken by something else

- GIVEN an unrelated program occupies the port
- WHEN the launcher starts
- THEN it MUST report the busy port and how to free it
- AND it MUST NOT start the server elsewhere without saying so

### Requirement: Browser opening

The launcher MUST open the browser only after the server answers, MUST probe over IPv4, and MUST honour the
automation opt-out.

#### Scenario: Normal start

- GIVEN the server answers 200 on `127.0.0.1:<port>`
- WHEN the launcher opens the browser
- THEN it MUST open `http://localhost:<port>`

#### Scenario: Automation opt-out

- GIVEN the variable `RIGUEL_SIN_NAVEGADOR` is set
- WHEN the launcher starts
- THEN no browser MUST be opened

### Requirement: Failures reach the user in plain language

The launcher MUST NOT let a Python traceback reach the user for any failure it can catch. One failure it
cannot catch is documented instead of handled: without its `_internal` folder, PyInstaller gives up before
any Python code runs.

#### Scenario: Unexpected failure inside the launcher

- GIVEN the launcher fails while preparing the database or starting the server
- WHEN the failure happens in Python
- THEN it MUST name what failed in plain language
- AND it MUST NOT print a bare traceback
