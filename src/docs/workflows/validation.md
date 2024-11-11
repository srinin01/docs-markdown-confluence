# Validation

The [validation.yml](/.github/workflows/validation.yml) workflow is used to run the following validation tools:
* Terraform configuration file formatting with `terraform fmt`
* Terraform configuration validation with `terraform validate`
* Terraform test with `terraform test`
* Python source code formatting with `python ruff format`
* Python source code validation with `python ruff check` with the rules: W,E,F,B,N,RET,SIM,G,TRY,LOG,RUF. Refer to the [ruff rule documentation](https://docs.astral.sh/ruff/rules/) for details of each rule/set. For additional rules to apply use `inputs.python_ruff_check_select`
* Python unit testing with `python -m coverage` (uses `run` and `report` sub commands)
  * `coverage report` by default will omit files with paths `*/tests/*` and will fail if coverage is less than `70` percent. These settings can be controlled with [pyproject.toml](#pyprojecttoml)
* Wiz CLI Scan
  * IaC

If the files fail the validation checks and the commit is part of a pull request then a comment will be added to the pull request with the output of the validation checks. Below is a simplified example of the comment contents:

```
Terraform formatting validation:
* main.tf

Python ruff validation:
* Would reformat: /home/runner/work/repo/repo/foo.py
* Would reformat: /home/runner/work/repo/repo/bar.py
2 files would be reformatted, 75 files already formatted.

The validation job may have additional details which can be downloaded here.
```

## Detailed Results

Some validation tools may output additional information that will not be displayed in the comment of a PR. If these logs exist then there will be a link to the action job and a direct download link for the output artifact at the bottom of the PR comment. Note that artifacts will eventually expire and their retention can be controlled by workflow input `artifact_retention_in_days` which defaults to 7 days.

## Usage

```yml
name: validation
on:
  pull_request:
jobs:
  validation:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/validation.yml@main
```

The resulting status checks can be used to block PRs by using the caller repository's branch protection. Similarly, other jobs may be dependent on this job by using [job dependencies as explained here](https://docs.github.com/en/actions/using-workflows/about-workflows#creating-dependent-jobs).

## Inputs

### General

* runs_on: Pass labels to the job's runs-on property. This value should stringified JSON and by default is `"['ubuntu-latest']"`
* environment: The github environment to use on job execution. This will set the sub claim in the OIDC auth when doing `inputs.do_aws_login=true`. By default is `validation`
* artifact_retention_in_days: Number of days to hold the detailed output as a job artifact. By default is `7`
* git_ops_aws_account: AWS account containing the AWS IAM OIDC role to assume. See [advance usage for details](#advanced-usage). By default is `467965917210` which is the Cyber SAE Ops account
* aws_region: The region to run AWS commands in. By default is `us-east-1`
* codeartifact_*: AWS CodeArtifact configuration if `inputs.do_aws_login=true` and `inputs.do_codeartifact_login=true`
* git_ssm_parameter_name: AWS SSM parameter in account `inputs.git_ops_aws_account` with github PAT. Defaults to `/github/cyber-ops/pat`
* do_aws_login: Do login to AWS using OIDC. By default is `true`
* do_codeartifact_login: Do the AWS CodeArtifact login and configuration of pip. Defaults to `true`
* do_git_credentials_ssm: Fetch the SSM parameter from `inputs.git_ssm_parameter_name`. By default is `true`
* do_git_credentials: Sets the github.com credential config with `inputs.do_git_credentials_ssm` if `inputs.git_ssm_parameter_name=true` or with `secrets.git_token`

### Terraform

* terraform_version: The Terraform binary version to use
* terraform_chdir: Terraform directory to change to when running Terraform commands. By default is `"./"`
* do_terraform_fmt: Run terraform format. By default is `true`
* do_terraform_validate: Run terraform validate. By default is `true`
* do_terraform_test: Run the terraform tests. By default is `true`

### Python

* python_version: Python version to use. By default is `"3.11"`
* python_ruff_version: Python ruff version to use. By default is `""` which will install latest
* python_ruff_select: Additional ruff rule sets to use. By default is `W` (cannot be empty)
* python_requirements: Path to Python requirements. By default is `requirements.txt`
* python_coverage_requirements: Path to Python requirements for unit testing such as mocking libraries. The following are installed by default and do not need to be specified unless pinning to non-latest: `coverage`, `pytest`. By default is `requirements-dev.txt`
* do_python_ruff_fmt: Run Python ruff format. By default is `true`
* do_python_ruff_check: Run Python ruff check. By default is `true`
* do_python_coverage: Run Python coverage unit testing. By default is `true`

### Wiz

* do_wiz_cli_iac_scan: Run the Wiz IaC scan. This requires the Wiz related secrets to be passed to the workflow file. By default is `false`
* wiz_cli_iac_policy: Wiz policy to apply for scan. By default is `Default IaC policy`
* wiz_cli_scan_path: The relative path in the repo to scan for Wiz CLI IaC scan. By default is `.`

#### pyproject.toml

Individual Python tools may be configured through a pyproject.toml file at the root of the caller repository.

For `ruff check` rule ignoring you must use:
```txt
[tool.ruff.lint.per-file-ignores]
"path/to/file" = [
  "E501",
  "N805",
]
```

This is due to the way ruff loads settings and the action job setting the CLI argument `--select`. Because the rule set selection is defined on the CLI any options set in a toml file for `[tool.ruff.lint]` will be ignored. For rule ignores you can use the `[tool.ruff.lint.per-file-ignores]` workaround above but for additional rule selection per repository you must use the action job's `inputs.python_ruff_check_select` which sets the `--extend-select` ruff CLI argument. Callers cannot modify the minimum applied rule set. The default rule is defined [here](#validation).

## Advanced Usage

By default the validation workflow does a login to the AWS account defined at `inputs.git_ops_aws_account` using github OIDC. The assumed role must be named `arn:aws:iam:$account::role/$git_owner/$git_repo` and here is a full example: `arn:aws:iam::467965917210:role/NBCUniversal/cyber-dynamic-list-api`.

### CodeArtifact

CodeArtifact is configured for pip using the `input.codeartifact*` action inputs after AWS login if `inputs.do_aws_login=true`. This may be required if your Python project requires privately published packages.

### Git Credentials

Git credentials can be configured for the validation workflow using `input.do_git_credentials=true` which by default will run and use AWS SSM parameter `inputs.git_ssm_parameter_name` (note that this requires `inputs.do_aws_login=true`). The token from the parameter will then be set for github.com calls. Alternatively you can pass `secret.git_token` to the action if your repository does not have an [AWS IAM github OIDC role](#advanced-usage).

## Warnings

The following are some general warnings of configurations where there can be unexpected behavior:
* `terraform test`
  * If using a `inputs.terraform_version` of `0.15 <= x < 1.6` then the `terraform test` step will exit with code zero but will give a warning
  * If using a `inputs.terraform_version` of `x < 0.15` then the `terraform test` step may exit non-zero and fail
