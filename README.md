# NeuraReview - AI-Powered Code Review Agent

**NeuraReview** is a state-of-the-art, AI-powered code review agent that automatically analyzes GitHub pull requests, identifies issues, and provides actionable, context-aware feedback. It helps development teams improve code quality, enhance security, and accelerate the review process.

---

## 🚀 Key Features

- **🤖 Intelligent Code Analysis**: Leverages GPT-4o for deep, context-aware analysis of code changes.
- **🎯 Precise Commenting**: Pinpoints the exact line of code for each comment, eliminating confusion.
- **✅ Actionable Suggestions**: Provides clean, pure-code suggestions in GitHub's native format, ready for one-click application.
- **🔍 Focused Reviews**: Only flags critical issues (security, memory, performance, bugs) - no noise!
- **📈 Severity Categorization**: Classifies issues as Critical, High, Medium, or Low to prioritize fixes.
- **🔌 Seamless GitHub Integration**: Fetches PRs, posts reviews, and integrates smoothly into your workflow.
- **⚡ GitHub Action Ready**: Use as a GitHub Action with just a comment trigger!
- **🔧 Highly Configurable**: Easily customize review parameters, skip specific file types, and more.
- **🛡️ Dry Run Mode**: Preview the review comments in your terminal before posting to GitHub.
- **🗣️ Multi-Language Support**: Expert analysis for a wide range of programming languages.

---

## 🛠️ How It Works

NeuraReview follows a robust, multi-step process to deliver high-quality code reviews:

1.  **Fetch PR Data**: Connects to the GitHub API to retrieve all files and changes associated with a pull request.
2.  **Parse Diffs**: Analyzes the diff for each file, creating a precise line-by-line map of all additions, deletions, and context lines. This map is crucial for accurate comment placement.
3.  **AI Analysis**: For each file, a detailed prompt is sent to the AI model (GPT-4o). The prompt includes the code changes, surrounding context, and strict instructions for providing high-quality feedback and pure-code suggestions.
4.  **Process Feedback**: The AI's JSON response is parsed into structured data, including issue descriptions, severity levels, and code suggestions.
5.  **Clean Suggestions**: Each suggestion is passed through a cleaning function to remove any extra text, comments, or markdown, ensuring it is 100% pure code.
6.  **Post Review**: The formatted comments and suggestions are posted to the pull request, with each comment placed on the exact line of code it refers to.

---

## ⚡ GitHub Action (Recommended)

The easiest way to use NeuraReview is as a GitHub Action. Just comment `/neurareview review` on any PR!

### Quick Setup

1. **Add the workflow** to your repository (`.github/workflows/neura-review.yml`):

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
python main_new.py --repo <owner/repo_name> --pr <pr_number>
```
*Example:*
```bash
python main_new.py --repo TimilsinaBimal/transformer --pr 1
```

### Dry Run (Recommended for first use)
Analyze a pull request and print the review to the console without posting it to GitHub. This is useful for previewing the results.

```bash
python main_new.py --repo <owner/repo_name> --pr <pr_number> --dry-run
```

### Analyze a Specific File
To focus the review on a single file within the pull request:

```bash
python main_new.py --repo <owner/repo_name> --pr <pr_number> --file <path/to/file>
```

### Verbose Mode
For detailed debugging output, including the full AI prompts and diff parsing information, use the `--verbose` flag.

```bash
python main_new.py --repo <owner/repo_name> --pr <pr_number> --verbose
```

---

## 📁 Project Structure

```
NeuraReview/
├── src/
│   ├── ai_reviewer.py       # Handles AI interaction and prompt engineering
│   ├── comment_manager.py   # Formats review comments and summaries
│   ├── config.py            # Manages configuration from environment variables
│   ├── diff_parser.py       # Parses diffs and maps line numbers to positions
│   ├── github_client.py     # Interacts with the GitHub API
│   ├── models.py            # Contains all data structures (dataclasses)
│   └── neura_review.py      # The main orchestrator for the review process
├── main.py              # The command-line interface (CLI) entry point
├── config.yaml              # Example configuration file (not used directly)
├── requirements.txt         # Project dependencies
└── README.md                # This file
```

---

## 🔮 Future Enhancements

- **GitHub Actions Integration**: Run NeuraReview automatically on every push to a pull request.
- **Support for Multiple AI Providers**: Add support for other models like Anthropic's Claude or Google's Gemini.
- **Custom Review Rules**: Allow teams to define their own project-specific review guidelines.
- **Batch Commenting**: Group related comments into a single thread to reduce notification noise.
- **UI Dashboard**: A web interface for viewing review history and analytics.

---
*NeuraReview - The future of automated code quality.*
