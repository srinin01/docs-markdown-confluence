# Confluence Docs

The [concfluence_docs.yml](/.github/workflows/confluence_docs.yml) workflow allows the publishing of Markdown and PNG files to Confluence from the /docs folder.

## Usage

```yml
name: Confluence
on:
  workflow_dispatch:
  push:
    branches:
    - main
jobs:
  publish:
    uses: NBCUniversal/cyber-git-actions/.github/workflows/terraform_cicd.yml@main
    secrets:
      confluence_bearer_token: ${{ secrets.CYBER_SAE_CORECLOUD_CONFLUENCE_TOKEN }}
      ssh_key: ${{ secrets.CYBER_SAE_CORECLOUD_ACTIONS_KEY }}
```

## Prerequisites

### Docs Folder

The /docs folder must exists, ex: REPO/docs/

### Confluence Bearer token

You will need a Confluence REST API bearer token saved as a Github Actions Secret with comment add/delete and attachement add/delete permissions.
