# NeuraReview - AI-Powered Code Review Agent

**NeuraReview** is a focused, AI-powered code review agent that automatically analyzes GitHub pull requests and identifies only critical issues. Unlike other review tools that flood you with style suggestions and minor improvements, NeuraReview focuses exclusively on security vulnerabilities, memory leaks, performance problems, and critical bugs that could cause real harm in production.

---

## 🚀 Key Features

- **🔍 Focused Reviews**: Only flags critical issues (security, memory, performance, bugs) - no noise!
- **🤖 Intelligent Analysis**: Leverages GPT-4o for deep, context-aware analysis of code changes.
- **⚡ GitHub Action Ready**: Use as a GitHub Action with just a comment trigger!
- **🎯 Precise Commenting**: Pinpoints the exact line of code for each comment, eliminating confusion.
- **✅ Actionable Suggestions**: Provides clean, pure-code suggestions in GitHub's native format, ready for one-click application.
- **📈 Severity Categorization**: Classifies issues as Critical, High, Medium, or Low to prioritize fixes.
- **🔌 Seamless GitHub Integration**: Fetches PRs, posts reviews, and integrates smoothly into your workflow.
- **🛡️ Dry Run Mode**: Preview the review comments in your terminal before posting to GitHub.
- **🗣️ Multi-Language Support**: Expert analysis for a wide range of programming languages.
- **🔧 Pre-commit Hooks**: Built-in code quality checks and formatting.

---

## 🛠️ How It Works

NeuraReview follows a focused, multi-step process to deliver high-quality code reviews that only flag critical issues:

1.  **Fetch PR Data**: Connects to the GitHub API to retrieve all files and changes associated with a pull request.
2.  **Parse Diffs**: Analyzes the diff for each file, creating a precise line-by-line map of all additions, deletions, and context lines.
3.  **AI Analysis**: For each file, a focused prompt is sent to the AI model (GPT-4o) that specifically looks for critical issues only - security vulnerabilities, memory leaks, performance problems, and critical bugs.
4.  **Filter Critical Issues**: Only issues with Critical or High severity are processed and included in the review.
5.  **Clean Suggestions**: Each suggestion is cleaned to remove any extra text, comments, or markdown, ensuring it is 100% pure code.
6.  **Post Review**: The formatted comments and suggestions are posted to the pull request, with each comment placed on the exact line of code it refers to.

---

## ⚡ GitHub Action (Recommended)

The easiest way to use NeuraReview is as a GitHub Action. Just comment `/neurareview review` on any PR!

### Quick Setup

1. **Add the workflow** to your repository (`.github/workflows/neura-review.yml`):

```yaml
name: Code Review

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

2. **Add your OpenAI API key** as a repository secret:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add `OPENAI_API_KEY` with your OpenAI API key

3. **Use it!** Comment `/neurareview review` on any pull request.

### What NeuraReview Reviews

✅ **Critical Issues Only:**
- Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
- Memory issues (leaks, buffer overflows, resource leaks)
- Performance problems (O(n²) algorithms, N+1 queries)
- Critical bugs (null pointer exceptions, race conditions)
- Error handling (missing try-catch blocks)

❌ **What It Ignores:**
- Code style and formatting
- Documentation suggestions
- Minor refactoring opportunities
- Educational comments

[📖 Full GitHub Action Documentation](ACTION_USAGE.md)

### Why NeuraReview is Different

Most code review tools overwhelm you with hundreds of style suggestions, documentation comments, and minor refactoring opportunities. NeuraReview takes a different approach:

- **🎯 Focused**: Only flags issues that could cause real problems in production
- **⚡ Fast**: No time wasted on style or documentation suggestions
- **🔍 Critical**: Security vulnerabilities, memory leaks, performance bottlenecks, and critical bugs
- **💡 Actionable**: Every comment includes a specific code suggestion you can apply immediately

### Example Output

When NeuraReview finds critical issues, it posts focused comments like:

```
🔴 🔒 Security Vulnerability

**Hardcoded API Key Detected**

The code contains a hardcoded API key which is a security risk. API keys should be stored in environment variables or secure configuration.

```suggestion
const apiKey = process.env.API_KEY;
```
```

When there are no critical issues, it simply says:

```
## ✅ No Critical Issues Found

Great job! No critical security, performance, or memory issues detected.
```

---

## ⚙️ Local Installation & Configuration

### 1. Prerequisites
- Python 3.8+
- Git

### 2. Installation Steps

```bash
# Clone the repository
git clone https://github.com/TimilsinaBimal/neurareview.git
cd neurareview

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt
```

### 3. Configuration

You must provide your GitHub and OpenAI API keys as environment variables.

```bash
# Set the required environment variables
export GITHUB_TOKEN="ghp_YourGitHubPersonalAccessToken"
export OPENAI_API_KEY="sk-YourOpenAI_API_Key"
```

> **Note:** For security, it is recommended to add these `export` commands to your shell's configuration file (e.g., `.zshrc`, `.bashrc`) or use a tool like `direnv` to manage environment variables per project.

---

## 🚀 Usage

NeuraReview is run from the command line.

### Basic Review
This command will fetch the specified pull request, analyze the changes, and post a review to GitHub.

```bash
python -m src.cli --repo <owner/repo_name> --pr <pr_number>
```
*Example:*
```bash
python -m src.cli --repo TimilsinaBimal/transformer --pr 1
```

### Dry Run (Recommended for first use)
Analyze a pull request and print the review to the console without posting it to GitHub. This is useful for previewing the results.

```bash
python -m src.cli --repo <owner/repo_name> --pr <pr_number> --dry-run
```

### Analyze a Specific File
To focus the review on a single file within the pull request:

```bash
python -m src.cli --repo <owner/repo_name> --pr <pr_number> --file <path/to/file>
```

### Verbose Mode
For detailed debugging output, including the full AI prompts and diff parsing information, use the `--verbose` flag.

```bash
python -m src.cli --repo <owner/repo_name> --pr <pr_number> --verbose
```

---

## 📁 Project Structure

```
NeuraReview/
├── .github/
│   └── workflows/
│       └── neura-review.yml     # GitHub Action workflow
├── action/
│   └── action.yml               # GitHub Action definition
├── src/
│   ├── ai_reviewer.py           # Handles AI interaction and prompt engineering
│   ├── cli.py                   # Command-line interface entry point
│   ├── comment_manager.py       # Formats review comments and summaries
│   ├── config.py                # Manages configuration from environment variables
│   ├── diff_parser.py           # Parses diffs and maps line numbers to positions
│   ├── github_client.py         # Interacts with the GitHub API
│   ├── models.py                # Contains all data structures (dataclasses)
│   ├── neura_review.py          # The main orchestrator for the review process
│   └── prompt.md                # AI prompt template for focused reviews
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── Dockerfile                   # Docker container for GitHub Action
├── example-workflow.yml         # Copy-paste template for users
├── ACTION_USAGE.md              # GitHub Action documentation
├── main.py                      # Legacy CLI entry point
├── pyproject.toml               # Project configuration and dependencies
├── requirements.txt             # Project dependencies
└── README.md                    # This file
```

---

## 🔮 Future Enhancements

- **Support for Multiple AI Providers**: Add support for other models like Anthropic's Claude or Google's Gemini.
- **Custom Review Rules**: Allow teams to define their own project-specific review guidelines.
- **Batch Commenting**: Group related comments into a single thread to reduce notification noise.
- **UI Dashboard**: A web interface for viewing review history and analytics.
- **Integration with CI/CD**: Automatic reviews on every push to pull requests.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

*NeuraReview - Focused on what matters: critical code quality issues.*
