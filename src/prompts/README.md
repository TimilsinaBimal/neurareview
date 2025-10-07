# NeuraReview Prompts

This directory contains the system prompts used by NeuraReview for different review modes.

## Available Prompts

### `agentic_system_prompt.md`
The comprehensive system prompt for agentic review mode. This prompt:
- Explains the AI's capabilities and available tools
- Provides guidelines for strategic context gathering
- Sets expectations for review quality and focus areas
- Includes instructions for final analysis formatting

### `traditional_review_prompt.md`
The focused prompt for traditional review mode. This prompt:
- Focuses on critical issues only (security, bugs, performance)
- Provides clear severity guidelines
- Includes formatting instructions for suggestions
- Contains examples of proper review output

## Customizing Prompts

### Method 1: Edit Files Directly
Simply edit the `.md` files in this directory. Changes will be automatically loaded on the next review.

### Method 2: Programmatic Customization
```python
from src.prompt_manager import PromptManager

prompt_manager = PromptManager()

# Add a custom prompt
custom_prompt = """
You are a security-focused code reviewer.
Focus only on security vulnerabilities and potential exploits.
"""
prompt_manager.add_custom_prompt("security_only.md", custom_prompt)

# Use the custom prompt
security_prompt = prompt_manager.get_custom_prompt("security_only.md")
```

### Method 3: Environment-Specific Prompts
You can create different prompts for different environments or teams:
- `agentic_system_prompt_backend.md` - For backend-focused reviews
- `agentic_system_prompt_frontend.md` - For frontend-focused reviews
- `traditional_review_prompt_strict.md` - For stricter review standards

## Prompt Variables

### Traditional Review Prompt
- `{language}` - Replaced with the detected programming language

Example usage:
```python
prompt_manager = PromptManager()
python_prompt = prompt_manager.get_traditional_review_prompt("Python")
javascript_prompt = prompt_manager.get_traditional_review_prompt("JavaScript")
```

## Best Practices

### Writing Effective Prompts
1. **Be Specific**: Clear instructions lead to better results
2. **Provide Examples**: Show the AI exactly what you want
3. **Set Boundaries**: Clearly define what to focus on and what to ignore
4. **Use Consistent Formatting**: Help the AI understand structure
5. **Test Iteratively**: Refine prompts based on actual review results

### Agentic Prompts
- Explain each tool clearly with use cases
- Provide decision-making guidelines
- Set limits to prevent excessive context gathering
- Include examples of good vs. poor context usage

### Traditional Prompts
- Focus on critical issues only
- Provide clear severity definitions
- Include formatting requirements for suggestions
- Show examples of proper output structure

## Prompt Development Tips

### Testing New Prompts
1. Start with small, focused changes
2. Test on known problematic code samples
3. Compare results with previous prompt versions
4. Get feedback from team members

### Measuring Prompt Effectiveness
- **Precision**: Are flagged issues actually problems?
- **Recall**: Are important issues being missed?
- **Consistency**: Do similar issues get flagged consistently?
- **Actionability**: Are suggestions helpful and implementable?

### Common Pitfalls
- **Too Verbose**: Overly long prompts can confuse the AI
- **Too Vague**: Unclear instructions lead to inconsistent results
- **Contradictory Instructions**: Conflicting guidelines confuse the AI
- **Missing Context**: Not explaining the review environment or goals

## Advanced Features

### Conditional Logic
You can create prompts that adapt based on file types, project settings, or other factors:

```python
def get_adaptive_prompt(file_path: str, project_type: str) -> str:
    base_prompt = prompt_manager.get_agentic_system_prompt()

    if file_path.endswith('.py'):
        base_prompt += "\n\nPay special attention to Python-specific issues like duck typing and GIL considerations."
    elif file_path.endswith('.js'):
        base_prompt += "\n\nFocus on JavaScript-specific issues like async/await patterns and prototype pollution."

    if project_type == "web_security":
        base_prompt += "\n\nPrioritize security vulnerabilities, especially XSS, CSRF, and injection attacks."

    return base_prompt
```

### Multi-Language Support
Create language-specific variations of prompts for better results:
- `agentic_system_prompt_python.md`
- `agentic_system_prompt_javascript.md`
- `agentic_system_prompt_go.md`

## Contributing

When contributing new prompts:
1. Follow the existing naming conventions
2. Include clear documentation of the prompt's purpose
3. Provide examples of expected input/output
4. Test thoroughly before submitting
5. Update this README with any new prompt files
