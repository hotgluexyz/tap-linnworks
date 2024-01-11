# tap-linnworks

`tap-linnworks` is a Singer tap for Linnworks.

Built by the hotglue team.


## Configuration

### Accepted Config Options

 - application_id - Required: True - Your Linnworks Application ID
 - application_secret - Required: True - Your Linnworks Application Secret
 - installation_token - Required: True - Your Linnworks Application Installation Token
 - start_date - Required: True - A default fallback start date whenever a bookmark is not available

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-linnworks --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

## Usage

### Executing the Tap Directly

```bash
tap-linnworks --version
tap-linnworks --help
tap-linnworks --config CONFIG --discover > ./catalog.json
```

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-linnworks` CLI interface directly using `poetry run`:

```bash
poetry run tap-linnworks --help
```