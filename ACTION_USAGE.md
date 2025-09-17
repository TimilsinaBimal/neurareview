# NeuraReview GitHub Action

NeuraReview is an AI-powered code review bot that focuses on critical issues like security vulnerabilities, memory leaks, performance problems, and critical bugs.

## Features

- 🔍 **Focused Reviews**: Only flags critical issues that could cause real harm
- 🚀 **Easy Setup**: Just add a workflow file to your repository
- 💬 **Comment Triggered**: Run reviews by commenting `/neurareview review` on any PR
- 🔒 **Security Focused**: Identifies security vulnerabilities, memory leaks, and performance issues
- ⚡ **Fast**: Only reviews critical and high-severity issues

## Quick Start

### 1. Add the Workflow

Create `.github/workflows/neura-review.yml` in your repository:

```yaml
name: NeuraReview

on:
  issue_comment:
    types: [created, edited]

jobs:
  neura-review:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '/neurareview review')
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write
      issues: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Run NeuraReview
        uses: TimilsinaBimal/neurareview@main
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
          pr_number: ${{ github.event.issue.number }}
          repo_name: ${{ github.repository }}
```

### 2. Set Up Secrets

Add the following secrets to your repository:

- `OPENAI_API_KEY`: Your OpenAI API key for AI analysis

The `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 3. Use the Action

1. Open any pull request in your repository
2. Comment `/neurareview review` on the PR
3. The action will automatically run and post review comments

## What NeuraReview Reviews

### ✅ Critical Issues Only
- **Security vulnerabilities**: SQL injection, XSS, authentication bypass, hardcoded secrets
- **Memory issues**: Memory leaks, buffer overflows, resource leaks
- **Performance problems**: O(n²) algorithms, N+1 queries, blocking operations
- **Critical bugs**: Null pointer exceptions, race conditions, data corruption
- **Error handling**: Missing try-catch blocks, unhandled exceptions

### ❌ What It Ignores
- Code style and formatting
- Documentation suggestions
- Minor refactoring opportunities
- Educational comments
- Project-level architecture decisions

## Configuration

### Optional Parameters

You can customize the action with these optional parameters:

```yaml
- name: Run NeuraReview
  uses: TimilsinaBimal/neurareview@main
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    pr_number: ${{ github.event.issue.number }}
    repo_name: ${{ github.repository }}
    dry_run: 'false'  # Set to 'true' for preview mode
```

### Permissions

The action requires these permissions:
- `contents: read` - To read the repository code
- `pull-requests: write` - To post review comments
- `issues: write` - To read issue comments

## Example Output

When NeuraReview finds critical issues, it will post comments like:

```
🔴 🔒 Security Vulnerability

**Hardcoded API Key Detected**

The code contains a hardcoded API key which is a security risk. API keys should be stored in environment variables or secure configuration.

```suggestion
const apiKey = process.env.API_KEY;
```
```

## Troubleshooting

### Common Issues

1. **Action not triggering**: Make sure you comment `/neurareview review` exactly (case-sensitive)
2. **Permission denied**: Ensure the workflow has the required permissions
3. **OpenAI API errors**: Check that your `OPENAI_API_KEY` secret is correctly set

### Debug Mode

To see detailed logs, you can modify the workflow to include verbose output:

```yaml
- name: Run NeuraReview
  uses: TimilsinaBimal/neurareview@main
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    pr_number: ${{ github.event.issue.number }}
    repo_name: ${{ github.repository }}
    verbose: 'true'
```

## Contributing

Found a bug or want to contribute? Check out the [NeuraReview repository](https://github.com/TimilsinaBimal/neurareview).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
