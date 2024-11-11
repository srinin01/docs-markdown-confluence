# AWS CodeArtifact NPM

The [codeartifact_npm.yml](/.github/workflows/codeartifact_npm.yml) workflow allows the publishing of Node.js packages to AWS CodeArtifact.

## Usage

```yml
name: example
on:
  push:
    tags:
    - "v*.*.*"
jobs:
  publish:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/codeartifact_npm.yml@main
    with:
      node_version: "18"
```

## Installing Python Packages from CodeArtifact

> Please review [prerequisites](#prerequisites) before continuing.

[Configure your package manager](https://docs.aws.amazon.com/codeartifact/latest/ug/npm-auth.html#configure-npm-login-command) to use CodeArtifact.

```
aws codeartifact login --tool npm --domain ${domain} --domain-owner ${account} --repository ${codeartifact_repository}
```

Then use the tool normally.

```
npm install async
```

> Note that the login credential will expire after 12 hours by default and the session will have to be refreshed.

## Prerequisites

### Node.js

Follow [these instructions](https://docs.npmjs.com/creating-node-js-modules) for configuring a package for publishing.

### OIDC Role Permissions

See [CodeArtifact Python documentation](./codeartifact_python.md#oidc-role-permissions).

### CodeArtifact Domain and Repository Configuration

See [CodeArtifact Python documentation](./codeartifact_python.md#codeartifact-domain-and-repository-configuration).

Additionally, the repository should have an [upstream to npm-store](https://docs.aws.amazon.com/codeartifact/latest/ug/repos-upstream.html) so that users of the repository can install public packages such as `async`.
