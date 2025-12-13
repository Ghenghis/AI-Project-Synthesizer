# 🚀 CI/CD Guide

## Overview

The AI Project Synthesizer uses a sophisticated two-tier parallelization strategy to efficiently run **8,145+ tests** in under 10 minutes using GitHub Actions.

## Architecture

### Two-Tier Parallelization

1. **CI-Level Sharding** (Horizontal Scaling)
   - 10 parallel GitHub Actions jobs
   - Tests distributed by execution time (pytest-split)
   - Each shard runs ~815 tests

2. **Per-Job Parallelization** (Vertical Scaling)
   - 2 pytest-xdist workers per job
   - Matches GitHub's 2-core runner specs
   - ~400 tests per worker

```
┌─────────────────────────────────────────────────┐
│                 GitHub Actions                  │
├─────────────────────────────────────────────────┤
│  Shard 1  Shard 2  ...  Shard 10 (10 parallel)  │
│    (2 workers each)                           │
│     ├─ Worker 1  ├─ Worker 2                   │
│     └─ ~400 tests └─ ~400 tests               │
└─────────────────────────────────────────────────┘
```

## Performance

| Configuration | Expected Runtime | Parallelism |
|--------------|------------------|-------------|
| Sequential | 60-120 minutes | 1x |
| pytest-xdist only | 15-30 minutes | 4x |
| CI matrix only | 8-15 minutes | 10x |
| **Combined (current)** | **5-10 minutes** | **20x** |

## Workflow Stages

### 1. Prepare Stage
- Determines shard count (configurable)
- Outputs matrix for parallel jobs

### 2. Unit Tests Stage
- Runs in 10 parallel shards
- Duration-based test distribution
- Coverage collection per shard
- Automatic retries for flaky tests

### 3. Integration Tests Stage
- Separate job with PostgreSQL service
- Tests requiring external dependencies

### 4. E2E Tests Stage
- Full workflow tests
- Only runs on main branch pushes

### 5. Report Stage
- Aggregates coverage from all shards
- Publishes test results
- Uploads artifacts

## Local Development

### Running Tests Locally

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests (sequential)
pytest tests/

# Run with parallelization (local)
pytest tests/ -n auto

# Run specific shard (like CI)
pytest tests/ --splits 10 --group 1
```

### Generating Test Durations

For optimal CI performance, generate test durations monthly:

```bash
# Generate durations file
python scripts/generate_test_durations.py

# Commit to repository
git add .test_durations
git commit -m "Update test durations for CI"
git push origin master
```

## Configuration

### Key Files

- `.github/workflows/test-suite.yml` - Main workflow
- `pytest.ini` - Test configuration
- `pyproject.toml` - Coverage settings
- `tests/conftest.py` - Test fixtures and skip markers

### Customizing Shards

To change the number of shards:

1. Update `prepare` job in workflow:
   ```yaml
   echo 'unit=[1,2,3,4,5,6,7,8,9,10,11,12]' >> $GITHUB_OUTPUT
   ```

2. Update `max-parallel` strategy:
   ```yaml
   max-parallel: 12
   ```

3. Update pytest command:
   ```yaml
   --splits 12 \
   --group ${{ matrix.shard }} \
   ```

### Test Categories

```ini
[pytest]
markers =
    unit: Fast unit tests with no external dependencies
    integration: Tests requiring external services
    e2e: End-to-end workflow tests
    slow: Tests taking more than 10 seconds
    requires_autogen: Tests requiring AutoGen dependency
    requires_swarm: Tests requiring Swarm dependency
    requires_piper: Tests requiring Piper TTS binary
    requires_glm_asr: Tests requiring GLM ASR dependencies
```

## Optional Dependencies

Tests with optional dependencies automatically skip when packages aren't available:

- **AutoGen**: Multi-agent conversations
- **Swarm**: Lightweight agent handoff
- **Piper TTS**: Local neural TTS
- **GLM ASR**: Speech recognition

## Coverage

### Configuration

- Target: 80% coverage threshold
- Parallel collection enabled
- Relative paths for cross-machine compatibility
- Combined from all shards

### Viewing Reports

Coverage reports are uploaded as artifacts:
1. Go to Actions → Latest workflow run
2. Download `combined-coverage` artifact
3. Open `combined-coverage.xml` in your browser

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check `requirements.txt` includes all dependencies
   - Verify optional deps are installed with fallback

2. **Timeout Failures**
   - Increase timeout in pytest.ini
   - Check for infinite loops or blocking I/O

3. **Coverage Not Combining**
   - Ensure `relative_files = true` in pyproject.toml
   - Check all shards upload coverage artifacts

4. **Uneven Shard Distribution**
   - Regenerate test durations file
   - Check for very slow tests skewing distribution

### Debug Mode

To debug a specific shard locally:

```bash
# Run shard 3 with verbose output
pytest tests/ \
  --splits 10 \
  --group 3 \
  --splitting-algorithm least_duration \
  -v \
  --tb=long
```

## Best Practices

1. **Commit Test Durations**: Keep `.test_durations` updated
2. **Monitor Usage**: Track GitHub Actions minutes usage
3. **Use Path Filtering**: CI only runs on relevant file changes
4. **Fix Flaky Tests**: Use retries sparingly, fix root causes
5. **Review Coverage Reports**: Address coverage gaps regularly

## Scaling Considerations

### When to Increase Shards

- Test suite grows beyond 10,000 tests
- Average runtime exceeds 10 minutes
- GitHub Actions has available concurrent job slots

### Self-Hosted Runners

Consider when:
- Private repository with >$20/month usage
- Need specialized hardware (GPU, more RAM)
- Have existing infrastructure to utilize

### Cost Optimization

For private repositories:
- Current usage: ~100 minutes per run
- Free tier: 2,000 minutes/month
- ~20 full test runs per month included

## Monitoring

### Key Metrics

- Total test runtime
- Coverage percentage
- Flaky test count
- GitHub Actions usage

### Alerts

Set up GitHub Actions alerts for:
- Workflow failures
- Coverage drops below threshold
- Runtime exceeding 15 minutes

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Add appropriate markers (`@pytest.mark.unit`, etc.)
3. Consider test duration impact
4. Update documentation if adding new test categories

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).
