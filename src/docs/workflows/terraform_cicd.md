# Terraform CICD

The [terraform_cicd.yml](/.github/workflows/terraform_cicd.yml) workflow allows for Terraform deployments from a centralized "operations" AWS account.

## Usage

```yml
name: example
on:
  workflow_dispatch:
  push:
    branches:
    - main
    - staging
    - dev
    paths-ignore:
    - .github/**
jobs:
  plan:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      environment: ${{ github.ref_name }}
      do_git_credential_config: true
    secrets:
      git_token: ${{ secrets.GIT_TOKEN }}
  apply:
    needs: plan
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      terraform_cmd: apply
      do_git_credential_config: true
      environment: ${{ github.ref_name }}
    secrets:
      git_token: ${{ secrets.GIT_TOKEN }}
```

### Usage - Centralized Secrets

In scenarios where you have many repositories that require `secrets.git_token` but defining an organization level secret is not doable and repo specific secrets is not scalable then you may want to use `inputs.git_token_ssm_parameter_name` which will fetch a Personal Access Token stored in the ops account. An example job:

```yml
plan:
  uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
  with:
    environment: ${{ github.ref_name }}
    git_token_ssm_parameter_name: '/github/cyber-ops/pat'
    do_git_credential_config: true
```

> Note that `github.ref_name` resolves to the branch name of the commit.

### Usage - Self-Hosted Runners

You may pass labels for the job's runs-on property by providing `inputs.runs_on` in stringified JSON form.

```yml
plan:
  uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
  with:
    environment: ${{ github.ref_name }}
    runs_on: "['self-hosted','Cyber','SAECoreCloudEngineering','${{ github.run_id }}']"
```

> Note that the exact value for self-hosted runners in `inputs.runs_on` will depend on how you provision runners. **This workflow does not configure or setup self-hosted runners themselves.** But you should be able to pass any number of labels to the job's runs-on property with this input. 

## Inputs

* terraform_version: The Terraform binary version to use
* runs_on: Pass labels to the job's runs-on property. This value should stringified JSON and by default is `"['ubuntu-latest']"`
* actions_bucket: The name of the S3 bucket in the operations account used for artifacts (contains sensitive information)
* git_token_ssm_parameter_name: The SSM parameter name in the ops account to fetch a github Personal Access Token from.
* do_git_credential_config: Whether to configure the git credentials with `secrets.git_token`. This should be `true` when `secrets.git_token` is defined and your Terraform or repository contains references to other, private git sources
* terraform_cmd: The Terraform command to run such as plan or apply
* ops_account: The centralized operations account to assume role into using OIDC
* cache_dir: The directory to cache between jobs. This is useful if your terraform builds artifacts in plan that are used in apply such as Lambda source code archives/packages
* environment: The Github Action environment to use. This will determine what permissions you have within the ops account and what accounts you can deploy to
* role_duration_seconds: The AWS OIDC role assumption duration in seconds. This value defaults to an hour and its max value is controlled by the AWS IAM role configuration. This value is the maximum duration your workflows will be able to run due to it restricting your action's ability to write to the state file. Note that this parameter does not control your action's ability to build resources in the target account -- that will be controlled by your Terraform provider blocks.

> The order of precedence when passing in git tokens in ascending order is: the workflow job default token, inputs.git_token_ssm_parameter_name, secrets.git_token. Meaning if inputs.git_token_ssm_parameter_name and secrets.git_token are both defined then secrets.git_token will be used.

## Secrets

* git_token: Github Personal Access Token (PAT) to use for cloning. If this is defined then set `inputs.do_git_credential_config=true` to ensure the token is set for any API calls to github.com
* environment_variables: Stringified JSON of key-value pairs to set as environment variables. An example: `environment_variables: '{"KEY1":"${{ secrets.KEY1 }}","KEY2":"${{ secrets.KEY2 }}"}'`. Please note that the keys will be visible within the action logs but the values will be redacted or masked with `***`.

## Prerequisites

* [AWS-Github OIDC authentication](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) for the operations AWS account
    * For every repo using this Github Action workflow there must be a role in the operations account for it. For example, if `NBCUniversal/example` was using this workflow and AWS account `123456789123` was your centralized operations account then the role ARN would be `arn:aws:iam::123456789123:role/NBCUniversal/example`
    * The required permissions on the role may be found [here](#oidc-role-permissions)
* Additional AWS IAM roles must be deployed in remote accounts where the Terraform will be building resources. For an example cross account role see [cross account roles section](#cross-account-roles)
* S3 buckets for action artifacts and Terraform state files in the operations account
* If your Terraform or git repository requires cloning from other, private, git repositories then you will need to create a Github Personal Access Token (PAT) with the necessary read permissions and pass it in via `secrets.git_token` and set `with.do_git_credential_config=true`. The workflow will then use the token for any Terraform module fetching and git submodule cloning (recursively)
* If using the ops account to centrally store a github Personal Access Token for github action jobs then the SSM parameter must exist in us-east-1, be created prior to running any jobs that rely on it, and jobs that use it must specify `inputs.git_token_ssm_parameter_name`

## Cross Account Roles

To be able to deploy resources in remote accounts with Terraform you must create cross account role that trust the centralized operations account. Each cross account role should have a trust policy with the centralized operations account as a trusted principal. The permission set on the cross account role will need to cover all resources defined in your repositories deploying to the account (thus full admin may be applicable).

## OIDC Role Permissions

Each OIDC role (unique to each repository using the workflow as described in the [prerequisites](#prerequisites)) should have the following permissions.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::${state_bucket}/env:/${env}/${org}/${repo}/state.tfstate",
                "arn:aws:s3:::${actions_artifact_bucket}/artifacts/env:/${env}/${org}/${repo}/*"
            ],
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:${org}/${repo}:environment:${env}"
                }
            }
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "${ca_role_arn_for_given_env}",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:${org}/${repo}:environment:${env}"
                }
            }
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::${state_bucket}"
        }
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": "ssm:GetParameter",
            "Resource": "arn:aws:ssm:us-east-1:${account}:parameter/${inputs.git_token_ssm_parameter_name}"
        }
    ]
}
```

This policy allows Terraform to only assume a role to the deployment, cross account based on the Github Action environment in the sub claim. For example, if your action is using the `dev` environment in github then that action can only assume role for the account(s) listed in the resource definition of the statement with sub condition on `dev` (if no statement exists then the action cannot assume into any cross account). Add additional statements for each environment-to-cross-account as necessary (recommended to not list more than one account per statement).

The S3 access statement only allows access to the state file bucket in the operations account for the repository that triggered the action and for the given environment. Thus, `NBCUniversal/example` using the `dev` environment can only access the Terraform workspace `dev` state file and cannot access the `main` workspace file for the same repository or any other repository's workspace state files. A similar pattern is used for the action's artifact bucket -- this storage is required to hold sensitive information such as the Terraform plan.out which [should not be cached or stored as an artifact](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows) in the Github Action itself.

> Note not shown are any KMS permissions if the buckets are using KMS instead of SSE-S3. Also not shown are DynamoDB permissions for state file locking. You may also need to share Terraform state files between repositories (repo1 has the state for VPC configuration which is used in repo2) which can be added as additional `s3:GetObject` statements -- these should be scoped as strict as possible as the state files contain sensitive information (effectively giving repo2 read access into everything managed via Terraform in repo1).

## Demonstration

The following is an example of using the workflow to deploy infrastructure. This assumes the IAM roles have already been configured.

The repository will have the following files:

```
my-repo/
├─ .github/
│  ├─ workflows/
│  │  ├─ terraform_cicd.yml
├─ build/
│  ├─ dev/
│  │  ├─ main.tf
│  ├─ main/
│  │  ├─ main.tf
├─ .gitignore
├─ main.tf
├─ README.md
```

Where `.github/workflows/terraform_cicd.yml` contains:

```yml
name: Terraform
on:
  workflow_dispatch:
  push:
    branches:
    - main
    - dev
    paths-ignore:
    - .github/**
jobs:
  plan:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      environment: ${{ github.ref_name }}
      terraform_chdir: build/${{ github.ref_name}}
  apply:
    needs: plan
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    with:
      terraform_cmd: apply
      terraform_chdir: build/${{ github.ref_name}}
```

> Note that we do not use the git credential configuration parameters here because the project has no additional NBCUniversal github dependencies.

And where `main.tf` describes the infrastructure of your module/project and contains:

```hcl
resource "aws_sns_topic" "this" {
  name = var.name
  tags = var.tags
}

variable "name" {
  type = string
}

variable "tags" {
  type = map(string)
}
```

Finally, the `build/*/main.tf` files instantiate your module and describe a particular environment such as dev or main (production):

```hcl
module "this" {
  source = "../../"
  name   = "example"
  tags   = {
    owner = "john.doe@nbcuni.com"
  }
}
```

> Note that github branches, environments, and terraform workspaces all share the same name for consistency and IAM permission purposes. This means when working in the `build/dev/main.tf` file you are working in the terraform `dev` workspace which uses the github `dev` environment and is deployed when changes are made to the `dev` branch.
>> Also note that if using Terraform <1.4.0 then you will need to init the workspace before the first action run (this only has be to done once per repository per environment). You can do this on your machine by authenticating to the ops account (input.ops_account) and running the following from `build/$name/main.tf` `terraform init` and `terraform workspace new $name` where name is the name of the environment (example `dev`). Starting with TF core 1.4.0 this will no longer be necessary and TF will automatically create the workspace if it does not exist.

> Note that the terms `action` and `run` describe an invocation of the action workflow file and a `job` refers to a task or subprocess within each action. So an action may be made of up several jobs and each job may run concurrently or sequentially depending on how they are scheduled in the `.github/workflows/*.yml` file. In this case the jobs run sequentially with the terraform plan job always running before the terraform apply job.

When committing or pushing changes to the dev branch this will trigger the `.github/workflows/terraform_cicd.yml` action because the branch `dev` is listed as a `on.workflow_dispatch.push.branch`. This will start an action run under the "Actions" tab of the repository in the web console.

> Note that the run will start immediately unless you have setup environment protection rules. Each action uses a github environment of the same name as the branch (or can be directly controlled through the environment input on the workflow in `.github/workflows/terraform_cicd.yml` but there are also IAM considerations so it is highly recommend to use the branch name). If you do not need to gate the action (ie you want the action to run immediately without human intervention or approval) then nothing needs to be done -- git actions will create the environment if it is not already created. If you do want gating, then create the environment before running the action(s) by going to the repository in the web console and clicking on Settings > Environments > Create and name it exactly the branch that will trigger the action (those in the `on.workflow_dispatch.push.branch` section). After creating select each environment and toggle "Required reviewers" and select a Teams group that will be required to approve before the action is run. Each team member will get an email of the deployment run and request for review and only one approver is required per team listed.

The action run has two jobs:
  * plan: Terraform plan generates a graph of proposed changes which can be viewed in the job's output.
  * apply: Terraform applies the plan from the previous job. The output apply can be viewed in the job's output.

> To view the logs and output of a job click on the run and then on any job either via the navigator bar or the workflow visualization window.\

![context](/src/docs/images/actions/view_job.png)

> If you are using environments to gate deployments (ie require human approval before making changes) then your action will be in a pending state and a reviewer will need to go to the run and click on "review" and select either approve or reject. The reviewer should always check the plan output before approving or rejecting.

![context](/src/docs/images/actions/review_job.png)

An example of a making a change and following it through the pipeline:
1. Editing `build/dev/main.tf` and adding another tag key-value pair.

```hcl
module "this" {
  source = "../../"
  name   = "example"
  tags   = {
    owner = "john.doe@nbcuni.com"
    hello = "world"
  }
}
```

2. Committing these changes to the dev branch.
3. The action started automatically.
4. The terraform plan job is blocked by a requested review of the job.
5. A reviewer evaluates the git diff and approves of the terraform plan job. 
6. The terraform action starts the plan job and outputs its proposed changes.

```
Terraform will perform the following actions:

  # aws_sns_topic.this will be updated in-place
  ~ resource "aws_sns_topic" "this" {
        id                                       = "arn:aws:sns:us-east-1:086787441818:example"
        name                                     = "example"
      ~ tags                                     = {
          + "hello" = "world"
            # (1 unchanged element hidden)
        }
      ~ tags_all                                 = {
          + "hello" = "world"
            # (1 unchanged element hidden)
        }
        # (11 unchanged attributes hidden)
    }

```

7. The terraform apply job is blocked by a requested review of the job.
8. A reviewer evaluates the terraform plan output and approves of the terraform apply job.
9. The terraform action starts the apply job and outputs the changes.
10. The infrastructure has been successfully updated in the dev environment.
