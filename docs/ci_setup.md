# CI/CD Setup Guide

## Overview

This guide explains how to set up and use the continuous integration and deployment pipelines for the Virtual HIL Framework.

## Prerequisites

- GitHub repository
- GitHub Actions enabled
- `uv` package manager installed locally

## GitHub Actions Workflows

### Workflow Files

Located in `.github/workflows/`:

1. **`sil-ci.yml`** - Software-in-the-Loop CI
2. **`nightly-regression.yml`** - Nightly regression tests
3. **`manual-hil-test.yml`** - Manual HIL test trigger

### SIL CI Workflow

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Steps**:
1. Checkout code
2. Install `uv`
3. Set up Python 3.11
4. Install dependencies (`uv sync --dev`)
5. Run unit tests (`pytest`)
6. Run Robot Framework tests
7. Upload test reports

**Usage**: Automatic on push/PR

### Nightly Regression Workflow

**Triggers**:
- Scheduled: Daily at 2 AM UTC
- Manual: Via workflow dispatch

**Steps**:
1. Checkout code
2. Install dependencies
3. Run full test suite (all directories)
4. Generate coverage report
5. Upload to Codecov

**Usage**: Automatic nightly or manual trigger via GitHub UI

### Manual HIL Test Workflow

**Triggers**:
- Manual via workflow dispatch

**Parameters**:
- `test_suite`: Choose which suite to run
  - `functional`
  - `diagnostic`
  - `integration`
  - `fault_injection`
  - `all`

**Steps**:
1. Checkout code
2. Install dependencies
3. Start ECU simulators
4. Run selected test suite
5. Upload test results

**Usage**: Manual trigger via GitHub Actions UI

## Local Testing Before Push

### Run All Tests

```bash
# Install dependencies
uv sync --dev

# Run unit tests
uv run pytest tests/ -v

# Run Robot Framework tests
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports tests/
```

### Run Specific Test Suite

```bash
# Functional tests only
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports tests/functional/

# With specific tags
uv run robot --pythonpath ./libraries:./ecu_simulation --outputdir reports --include smoke tests/
```

### Generate Coverage Report

```bash
uv run pytest --cov=libraries --cov-report=html --cov-report=xml tests/
```

## CI Environment Variables

Available in GitHub Actions:

```yaml
env:
  PYTHON_VERSION: "3.11"
  UV_VERSION: "latest"
```

## Artifact Handling

### Test Reports

All workflows upload test reports as artifacts:

- **SIL CI**: `test-reports` - Contains output.xml, log.html, report.html
- **Nightly Regression**: `coverage-reports` - Contains coverage XML
- **Manual HIL**: `hil-test-results` - Contains full test output

### Accessing Artifacts

1. Go to Actions tab in GitHub
2. Select the workflow run
3. Scroll to "Artifacts" section
4. Download desired artifact

## Status Badges

Add to README.md:

```markdown
[![SIL CI](https://github.com/username/Virtual-HIL-Framework/actions/workflows/sil-ci.yml/badge.svg)](https://github.com/username/Virtual-HIL-Framework/actions/workflows/sil-ci.yml)
[![Nightly Regression](https://github.com/username/Virtual-HIL-Framework/actions/workflows/nightly-regression.yml/badge.svg)](https://github.com/username/Virtual-HIL-Framework/actions/workflows/nightly-regression.yml)
```

## Troubleshooting

### Common CI Issues

**Issue**: Tests timeout in CI but pass locally

**Solution**:
- Increase timeout in workflow
- Check for environment-specific timing issues
- Use `--timeout` option in Robot Framework

**Issue**: Dependency installation fails

**Solution**:
- Verify `uv.lock` is committed
- Check Python version compatibility
- Run `uv lock --upgrade` locally and commit

**Issue**: Cannot find modules

**Solution**:
- Verify PYTHONPATH includes correct directories
- Check `--pythonpath` argument in Robot command
- Ensure all files are committed

### Debug Failed CI Run

1. Download workflow logs
2. Check artifact reports (output.xml, log.html)
3. Reproduce locally with same Python version
4. Compare environment differences

## Adding New CI Steps

### Example: Add Linting

Add to `.github/workflows/sil-ci.yml`:

```yaml
- name: Run Ruff Linter
  run: |
    uv run ruff check .
    uv run ruff format --check .
```

### Example: Add Type Checking

```yaml
- name: Run MyPy
  run: |
    uv run mypy ecu_simulation/ libraries/
```

## Branch Protection Rules

Recommended settings for `main` branch:

1. **Require pull request reviews** - At least 1 approval
2. **Require status checks** - All CI must pass
3. **Require branches to be up to date** - Before merging

## Self-Hosted Runner Setup (Optional)

For running with actual CAN hardware:

### Prerequisites

- Linux machine with physical CAN interface
- Python 3.11 installed
- CAN driver (SocketCAN, etc.)

### Setup

1. Create self-hosted runner in GitHub repository settings
2. Install `uv` on runner
3. Configure CAN interface
4. Add label to runner (e.g., `can-hardware`)

### Usage in Workflow

```yaml
jobs:
  hardware-test:
    runs-on: [self-hosted, can-hardware]
    steps:
      - uses: actions/checkout@v4
      - name: Run Hardware Tests
        run: |
          uv run robot --pythonpath . --outputdir reports tests/hardware/
```

## Performance Optimization

### Parallel Test Execution

Split tests across multiple jobs:

```yaml
jobs:
  test-functional:
    runs-on: ubuntu-latest
    steps:
      - run: uv run robot tests/functional/

  test-diagnostic:
    runs-on: ubuntu-latest
    steps:
      - run: uv run robot tests/diagnostic/
```

### Caching

GitHub Actions automatically caches `uv` packages based on `uv.lock`.

## Monitoring and Alerts

### Notification Setup

Add to workflow YAML:

```yaml
- name: Notify on Failure
  if: failure()
  run: |
    # Send Slack notification
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -d '{"text":"Tests failed for Virtual HIL Framework"}'
```

## Best Practices

1. **Keep CI fast** - Only run necessary tests on PR
2. **Use caching** - Leverage uv's caching
3. **Matrix testing** - Test multiple Python versions if needed
4. **Artifact retention** - Configure appropriate retention period
5. **Secret management** - Use GitHub Secrets for sensitive data
6. **Documentation** - Keep workflow files well-commented
