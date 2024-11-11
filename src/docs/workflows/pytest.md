# Pytest

The [validation workflow file](./validation.md) contains a suite of tests that includes pytest but users may use this workflow instead for running just pytest. This may be useful for integration tests which may not be runnable from validation environments.

## Results

Output logs will be archived and downloadable on job failure. Note that artifacts will eventually expire and their retention can be controlled by workflow input `artifact_retention_in_days` which defaults to 7 days.

## Usage

Integration test configuration with a deployment build (this will run the integration tests after every deployment):

```yml
name: Terraform
on:
  workflow_dispatch:
  push:
    branches:
    - main
    tags:
    - 'v*.*.*'
    paths-ignore:
    - .github/**
    - CHANGELOG.md
jobs:
  plan:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      environment: ${{ endsWith(github.ref_name, '-rc') && 'staging' || startsWith(github.ref_name, 'v') && 'main' || 'dev' }}
      terraform_chdir: build/${{ endsWith(github.ref_name, '-rc') && 'staging' || startsWith(github.ref_name, 'v') && 'main' || 'dev' }}
      do_git_credential_config: true
      git_token_ssm_parameter_name: "/github/cyber-ops/pat"
  apply:
    needs: plan
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      terraform_cmd: apply
      environment: ${{ endsWith(github.ref_name, '-rc') && 'staging' || startsWith(github.ref_name, 'v') && 'main' || 'dev' }}
      terraform_chdir: build/${{ endsWith(github.ref_name, '-rc') && 'staging' || startsWith(github.ref_name, 'v') && 'main' || 'dev' }}
      do_git_credential_config: true
      git_token_ssm_parameter_name: "/github/cyber-ops/pat"
  integration_test:
    needs: apply
    uses: NBCUniversal/cyber-git-actions/.github/workflows/pytest.yml@main
    with:
        environment: ${{ endsWith(github.ref_name, '-rc') && 'staging' || startsWith(github.ref_name, 'v') && 'main' || 'dev' }}
```

> Note that if you have tests that are not production safe then you should use the [skipif](https://docs.pytest.org/en/stable/how-to/skipping.html#id1) pytest marker with the condition being `os.environ.get("TF_WORKSPACE", "dev") == "main"` where the env var `TF_WORKSPACE` will be equal to the GitHub Action job's `inputs.environment` value.

Unit test configuration (recommended to use the [validation workflow file](./validation.md) instead): 
```yml
name: unit tests
on:
  pull_request:
jobs:
  validation:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/pytest.yml@main
    with:
        python_ignore_paths: "['tests/integration']"
        python_test_path: "tests"
        python_stop_on_first_error: false
        environment: validation
```

## Inputs

### General

* runs_on: Pass labels to the job's runs-on property. This value should stringified JSON and by default is `"['ubuntu-latest']"`
* environment: The github environment to use on job execution. This will set the sub claim in the OIDC auth when doing `inputs.do_aws_login=true`. By default is `validation`
* artifact_retention_in_days: Number of days to hold the detailed output as a job artifact. By default is `7`
* git_ops_aws_account: AWS account containing the AWS IAM OIDC role to assume. See [advance usage for details](#advanced-usage). By default is `467965917210` which is the Cyber SAE Ops account
* aws_region: The region to run AWS commands in. By default is `us-east-1`
* codeartifact_*: AWS CodeArtifact configuration if `inputs.do_aws_login=true` and `inputs.do_codeartifact_login=true`

### Python

* python_version: Python version to use. By default is `"3.11"`
* python_requirements: Path to Python requirements. By default is `requirements.txt`
* python_requirements_dev: Path to Python requirements for testing such as mocking packages. The following are installed by default and do not need to be specified unless pinning to non-latest: `coverage`, `pytest`. By default is `requirements-dev.txt`
* python_stop_on_first_error: Stop on the first test to fail. This is useful for integration tests which might have to execute in a specific order - on first failure there is no point in continuing downstream tests. By default is `true`
* python_test_path: Path to run pytest on. By default is `tests/integration/`
* python_ignore_paths: List of paths as stringified JSON to ignore. By default is `[]`


### CodeArtifact

CodeArtifact is required and configured for pip using the `input.codeartifact*` action inputs.

> Note that private github published packages will fail (ex inside your requirements.txt is a line like `git+https://github.com/foo/bar@main` where repository bar is private within owner foo). These packages will need to be published to CodeArtifact which can be done with the [codeartificat_python](./codeartifact_python.md) workflow file.
