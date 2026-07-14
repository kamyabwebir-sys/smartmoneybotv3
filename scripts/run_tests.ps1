param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

if ($VerboseOutput) {
    python -m pytest -vv
}
else {
    python -m pytest
}
