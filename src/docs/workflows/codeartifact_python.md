# AWS CodeArtifact Python

The [codeartifact_python.yml](/.github/workflows/codeartifact_python.yml) workflow allows the building and publishing of Python packages to AWS CodeArtifact.

## Usage

```yml
name: example
on:
  push:
    tags:
    - "v*.*.*"
jobs:
  publish:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/codeartifact_python.yml@main
    with:
      python_version: "3.9"
```

## Installing Python Packages from CodeArtifact

> Please review [prerequisites](#prerequisites) before continuing.

[Configure your package manager](https://docs.aws.amazon.com/codeartifact/latest/ug/python-configure-pip.html) to use CodeArtifact.

```
aws codeartifact login --tool pip --domain ${domain} --domain-owner ${account} --repository ${codeartifact_repository}
```

Then use the tool normally.

```
pip install requests, splunk-python-client
```

> Note that the login credential will expire after 12 hours by default and the session will have to be refreshed.

## Prerequisites

### Python setup.py

The Python project should be using a [setup.py file](https://docs.python.org/3/distutils/setupscript.html) at the root of the repository for building the package. The git action will call `python setup.py sdist` to build the package archive for upload to CodeArtifact (archive expected at `dist/`).

### OIDC Role Permissions

An OIDC github role must be deployed with the following trust policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${account}:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": [
                        "repo:${org}/${repo1}:*",
                        "repo:${org}/${repo2}:*",
                    ]
                }
            }
        }
    ]
}
```

And the role should have the following permissions policy for publishing.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "codeartifact:ListRepositoriesInDomain",
                "codeartifact:GetDomainPermissionsPolicy",
                "codeartifact:GetAuthorizationToken",
                "codeartifact:DescribeDomain"
            ],
            "Resource": "arn:aws:codeartifact:${region}:${account}:domain/${domain}"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "codeartifact:PutPackageMetadata",
                "codeartifact:PublishPackageVersion",
                "codeartifact:ListPackageVersions",
                "codeartifact:ListPackageVersionDependencies",
                "codeartifact:ListPackageVersionAssets",
                "codeartifact:GetPackageVersionReadme",
                "codeartifact:DescribePackageVersion"
            ],
            "Resource": "arn:aws:codeartifact:${region}:${account}:package/${domain}/${artifact_repository}/*"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "codeartifact:ReadFromRepository",
                "codeartifact:ListPackages",
                "codeartifact:GetRepositoryEndpoint",
                "codeartifact:DescribeRepository"
            ],
            "Resource": "arn:aws:codeartifact:${region}:${account}:repository/${domain}/${artifact_repository}"
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": "sts:GetServiceBearerToken",
            "Resource": "*"
        }
    ]
}
```

### CodeArtifact Domain and Repository Configuration

The AWS CodeArtifact domain should have the following resource policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": [
                "codeartifact:ListRepositoriesInDomain",
                "codeartifact:GetDomainPermissionsPolicy",
                "codeartifact:GetAuthorizationToken",
                "codeartifact:DescribeDomain"
            ],
            "Resource": "arn:aws:codeartifact:${region}:${account}:domain/${domain}",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalOrgID": [
                        "o-xxx1",
                        "o-xxx2"
                    ]
                }
            }
        }
    ]
}
```

This will allow all organization accounts to authenticate to the domain and list the domain's repositories.

The repository should have the following resource policy.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": [
                "codeartifact:ReadFromRepository",
                "codeartifact:ListPackages",
                "codeartifact:ListPackageVersions",
                "codeartifact:ListPackageVersionDependencies",
                "codeartifact:ListPackageVersionAssets",
                "codeartifact:GetRepositoryEndpoint",
                "codeartifact:GetPackageVersionReadme",
                "codeartifact:DescribeRepository",
                "codeartifact:DescribePackageVersion"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:PrincipalOrgID": [
                        "o-xxx1",
                        "o-xxx2"
                    ]
                }
            }
        },
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::${account}:root"
            },
            "Action": [
                "codeartifact:PutPackageMetadata",
                "codeartifact:PublishPackageVersion"
            ],
            "Resource": "*"
        }
    ]
}
```

This will allow all organization accounts to get repository packages for use in their builds but only allow the the account `${account}` to publish and update packages.

Additionally, the repository should have an [upstream to pypi](https://docs.aws.amazon.com/codeartifact/latest/ug/repos-upstream.html) so that users of the repository can install public packages such as `requests`.
