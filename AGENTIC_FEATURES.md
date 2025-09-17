# 🤖 Agentic Code Review Features

NeuraReview now includes powerful **agentic capabilities** that allow the AI to intelligently gather additional context from your codebase before providing reviews. This leads to more comprehensive, accurate, and contextually-aware code reviews.

## 🎯 What is Agentic Review?

Traditional code review tools only see the diff - the lines that changed. Our agentic system gives the AI the ability to:

1. **Analyze the initial diff**
2. **Decide if more context is needed**
3. **Gather specific additional information** using context tools
4. **Iterate** until it has sufficient understanding
5. **Provide comprehensive feedback** based on all available context

## 🛠️ Available Context Tools

The AI agent has access to these tools to gather context:

### `get_file_content`
- Read specific files from the repository
- Can limit to specific line ranges
- Perfect for examining related files mentioned in imports

### `search_codebase`
- Search across the entire codebase for patterns
- Find function calls, class usage, variable references
- Filter by file extension

### `find_function_definition`
- Locate complete function definitions
- Understand function signatures and implementations
- See how functions are supposed to be used

### `find_class_definition`
- Find class definitions with methods and attributes
- Understand inheritance hierarchies
- Check interface contracts

### `find_import_usages`
- Find all files that import a specific module
- Understand the impact of changes to shared code
- Identify potential breaking changes

### `find_test_files`
- Locate test files related to source files
- Check if changes might break existing tests
- Identify missing test coverage

## 🚀 Key Benefits

### 1. **Breaking Change Detection**
The AI can examine how functions/classes are used across the codebase and identify potential breaking changes:

```python
# If you change a function signature:
def calculate_total(items, tax_rate=0.1):  # Added tax_rate parameter

# The AI will:
# 1. Search for all usages of calculate_total
# 2. Check if they handle the new parameter
# 3. Flag potential breaking changes
```

### 2. **Consistency Enforcement**
The AI learns project patterns and enforces consistency:

```python
# If you add a new authentication method:
class NewAuthProvider(AuthProvider):

# The AI will:
# 1. Find the base AuthProvider class
# 2. Check existing auth implementations
# 3. Ensure your implementation follows the same patterns
# 4. Suggest missing methods or inconsistencies
```

### 3. **Integration Validation**
The AI understands how changes fit into the broader system:

```python
# If you modify a database model:
class User(Model):
    email = EmailField(unique=True)  # Added unique constraint

# The AI will:
# 1. Search for User model usage
# 2. Check migration implications
# 3. Look for related test files
# 4. Identify potential data integrity issues
```

## 📊 Example Agentic Review Flow

Here's how the AI might review a complex change:

### Initial Analysis
```
AI: "I see you've added a new payment method. Let me understand the existing payment architecture."
```

### Context Gathering - Iteration 1
```
AI calls: find_class_definition("PaymentMethod")
Result: Found base PaymentMethod class with process() and validate() methods

AI calls: search_codebase("PaymentMethod", ".py")
Result: Found 5 existing implementations: CreditCardPayment, PayPalPayment, etc.
```

### Context Gathering - Iteration 2
```
AI calls: find_test_files("src/payments.py")
Result: Found tests/test_payments.py with test patterns for payment methods

AI calls: get_file_content("tests/test_payments.py", start_line=1, end_line=50)
Result: Sees test structure and required test methods
```

### Final Review
```
✅ The AI now provides comprehensive feedback:

1. **Missing Method**: Your new CryptoPayment class is missing the validate() method required by PaymentMethod base class.

2. **Test Coverage**: Based on existing payment method tests, you should add:
   - test_crypto_payment_success()
   - test_crypto_payment_invalid_wallet()
   - test_crypto_payment_insufficient_funds()

3. **Security Concern**: Other payment methods sanitize user input in validate(). Consider adding similar validation for wallet addresses.

4. **Integration**: The PaymentProcessor.get_available_methods() should be updated to include crypto payments.
```

## ⚙️ Configuration

### Enable/Disable Agentic Review

```yaml
# config.yaml
ai:
  enable_agentic_review: true  # Set to false for traditional review
  max_context_iterations: 5   # Max rounds of context gathering
  max_context_calls_per_iteration: 3  # Max tool calls per round
```

### Multiple AI Provider Support

```yaml
ai:
  provider: "openai"  # Currently supported: openai
  model: "gpt-4o"     # or "gpt-5-mini" for reasoning models
  # Future providers: anthropic, google, azure, etc.
```

## 🔧 Usage Examples

### Standard Agentic Review
```bash
python main.py --repo owner/repo --pr 123
```

### Dry Run (See What Would Be Posted)
```bash
python main.py --repo owner/repo --pr 123 --dry-run
```

### Single File Analysis
```bash
python main.py --repo owner/repo --pr 123 --file src/models.py
```

### Traditional Review (No Context Gathering)
```bash
# Set enable_agentic_review: false in config
python main.py --repo owner/repo --pr 123
```

## 🎛️ Advanced Configuration

### Fine-tuning Context Gathering

```python
# For simple changes, reduce iterations to save API calls
ai:
  max_context_iterations: 2
  max_context_calls_per_iteration: 2

# For complex architectural changes, increase limits
ai:
  max_context_iterations: 8
  max_context_calls_per_iteration: 5
```

### Custom AI Providers

The system is designed to support multiple AI providers:

```python
from src.ai_provider_factory import AIProviderFactory
from src.ai_providers.base import AIProvider

# Register a custom provider
class CustomAIProvider(AIProvider):
    # Implement required methods
    pass

AIProviderFactory.register_provider("custom", CustomAIProvider)
```

## 📈 Performance Considerations

### API Usage
- Agentic review uses more API calls but provides much better quality
- Context gathering is cached per PR to avoid redundant calls
- Smart iteration limits prevent runaway context gathering

### Concurrency
- Agentic analysis uses lower concurrency (2 files at once) due to complexity
- Traditional review uses higher concurrency (5 files at once)
- Context tool calls are parallelized within each iteration

### Cost Optimization
- AI only gathers context when truly needed
- Configurable limits prevent excessive API usage
- Caching reduces redundant file fetches

## 🔍 Monitoring and Debugging

### Verbose Logging
```bash
python main.py --repo owner/repo --pr 123 --verbose
```

### Understanding AI Decisions
The AI logs its reasoning:
```
INFO: Agentic analysis iteration 1 for src/models.py
INFO: AI called get_file_content for src/base_models.py
INFO: AI called find_test_files for src/models.py
INFO: Agentic analysis found 3 issues in src/models.py
```

## 🚀 Future Enhancements

### Planned Features
- **Multi-file Analysis**: Analyze changes across multiple related files as a unit
- **Historical Context**: Learn from past changes and reviews in the repository
- **Custom Tools**: Allow teams to define project-specific context gathering tools
- **Smart Caching**: More sophisticated caching strategies for better performance
- **Review Templates**: AI learns team-specific review patterns and preferences

### Additional AI Providers
- Anthropic Claude
- Google Gemini
- Azure OpenAI
- Local/Self-hosted models

## 📚 Best Practices

### 1. **Start with Defaults**
The default configuration works well for most projects. Only tune if needed.

### 2. **Monitor API Usage**
Keep an eye on API costs, especially for large PRs with many files.

### 3. **Use Dry Runs**
Always test with `--dry-run` first to see what the AI will post.

### 4. **Gradual Rollout**
Start with agentic review on smaller PRs, then expand to larger changes.

### 5. **Team Training**
Help your team understand that reviews may take slightly longer but will be much more comprehensive.

---

The agentic review system represents a significant leap forward in automated code review quality. By giving the AI the ability to understand context, we can catch issues that would be impossible to detect from diffs alone.
