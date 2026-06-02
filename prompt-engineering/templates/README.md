# Prompt Templates

Reusable, versioned prompt templates for production systems.

## Overview

Templates enable:
- **Reusability**: DRY principle for prompts
- **Versioning**: Track prompt changes over time
- **A/B Testing**: Compare prompt variants
- **Maintainability**: Central repository of prompts

## Structure

```
templates/
├── README.md
├── template_system.py      # Template loader and manager
├── meta_prompts.py          # Prompts that generate prompts
├── system_messages.py       # Role definitions and personas
└── tests/
```

## Components

### 1. Template System (`template_system.py`)
Load and render Jinja2 templates with variables.

**Features:**
- File-backed templates
- Variable substitution
- Versioning by hash
- Template registry

**Example:**
```python
from prompt_engineering.templates import template_system

prompt = await template_system.load(
    "sentiment_analysis",
    text="I love this!",
    format="JSON"
)
```

### 2. Meta-Prompts (`meta_prompts.py`)
Prompts that generate or optimize other prompts.

**Use cases:**
- Automatic prompt generation for new tasks
- Prompt optimization and refinement
- Prompt compression
- Few-shot example generation

**Example:**
```python
from prompt_engineering.templates import meta_prompts

optimized = await meta_prompts.optimize_prompt(
    task="sentiment classification",
    current_prompt="Classify this text...",
    examples=training_data
)
```

### 3. System Messages (`system_messages.py`)
Pre-built role definitions and personas.

**Roles:**
- Technical Assistant
- Research Analyst
- Code Reviewer
- Customer Support
- Data Scientist
- Product Manager

**Example:**
```python
from prompt_engineering.templates import system_messages

system_msg = system_messages.get_role("data_scientist")
# Returns: "You are an expert data scientist with deep knowledge..."
```

## Template Format

Templates use Jinja2 syntax:

```jinja2
# templates/sentiment_analysis.jinja2

You are a sentiment analysis expert.

Analyze the sentiment of the following text and classify it as:
- Positive
- Negative
- Neutral

{% if examples %}
Examples:
{% for example in examples %}
Input: {{ example.input }}
Output: {{ example.output }}

{% endfor %}
{% endif %}

Now analyze:
Input: {{ text }}
Output:
```

## Template Best Practices

### Do ✅
- Use templates for repeated prompt patterns
- Version templates with hashes
- Include variable validation
- Document required variables
- Test templates with edge cases
- Track performance per template

### Don't ❌
- Don't hard-code business logic in templates
- Don't create templates for one-off tasks
- Don't skip version tracking
- Don't forget fallback defaults
- Don't use overly complex Jinja2 logic

## Versioning Strategy

```python
# Hash-based versioning
template_hash = sha256(content).hexdigest()[:8]
version = f"{date}-{hash}"  # e.g., "20240115-a3f2b9c1"

# A/B testing
template_system.deploy(
    name="sentiment_analysis",
    version_a="20240115-a3f2b9c1",
    version_b="20240116-b7d8e2f3",
    traffic_split=0.5  # 50/50 split
)
```

## Meta-Prompting Patterns

### 1. Prompt Generation
Generate task-specific prompts automatically:

```python
task = "Extract product features from reviews"
prompt = await meta_prompts.generate_prompt(task)
```

### 2. Prompt Optimization
Optimize existing prompts for better performance:

```python
optimized = await meta_prompts.optimize_prompt(
    current_prompt="Classify sentiment...",
    examples=train_data,
    metric="accuracy"
)
```

### 3. Few-Shot Example Generation
Generate synthetic examples:

```python
examples = await meta_prompts.generate_examples(
    task="sentiment_analysis",
    num_examples=5
)
```

## System Message Library

Pre-built personas for common roles:

| Role | Use Case | Tone |
|------|----------|------|
| `technical_assistant` | Technical Q&A | Professional, precise |
| `research_analyst` | Research tasks | Analytical, thorough |
| `code_reviewer` | Code review | Critical, constructive |
| `customer_support` | Customer service | Friendly, helpful |
| `data_scientist` | Data analysis | Technical, clear |
| `product_manager` | Product decisions | Strategic, user-focused |
| `creative_writer` | Content creation | Creative, engaging |
| `educator` | Teaching/explaining | Patient, clear |

## Template Registry

All templates stored in `prompts/` directory:

```
prompts/
├── sentiment_analysis.jinja2
├── entity_extraction.jinja2
├── summarization.jinja2
├── qa_with_context.jinja2
├── code_generation.jinja2
└── text_classification.jinja2
```

Access via registry:

```python
# List all templates
templates = await template_system.list_templates()

# Get template metadata
metadata = await template_system.get_metadata("sentiment_analysis")

# Get template versions
versions = await template_system.list_versions("sentiment_analysis")
```

## Performance Tracking

Track template performance:

```python
# Log template usage
await template_system.log_usage(
    template_name="sentiment_analysis",
    version="20240115-a3f2b9c1",
    tokens=450,
    cost=0.0003,
    latency_ms=320,
    quality_score=0.92
)

# Get template stats
stats = await template_system.get_stats("sentiment_analysis")
# {
#   "total_uses": 1247,
#   "avg_tokens": 450,
#   "avg_cost": 0.0003,
#   "avg_quality": 0.91,
#   "p95_latency_ms": 420
# }
```

## A/B Testing

Compare template variants:

```python
# Deploy A/B test
await template_system.ab_test(
    name="sentiment_analysis",
    variant_a="20240115-a3f2b9c1",
    variant_b="20240116-b7d8e2f3",
    metric="accuracy",
    duration_days=7
)

# Get A/B test results
results = await template_system.get_ab_results("sentiment_analysis")
# {
#   "variant_a": {"accuracy": 0.87, "cost": 0.0003},
#   "variant_b": {"accuracy": 0.91, "cost": 0.0004},
#   "winner": "variant_b",
#   "confidence": 0.95
# }
```

## Interview Questions

### Junior Level
1. **What is a prompt template?** Reusable prompt pattern with variables that can be filled in.
2. **Why version prompts?** Track changes, A/B test, rollback if needed.
3. **What's Jinja2?** Template engine for variable substitution.

### Mid Level
4. **How do you implement prompt versioning?** Hash content, track by date-hash, store metadata.
5. **Explain meta-prompting.** Using LLMs to generate or optimize prompts for other tasks.
6. **How to A/B test prompts?** Deploy variants, split traffic, measure metrics, choose winner.

### Senior Level
7. **Design a prompt management system.** Registry + versioning + A/B testing + performance tracking + rollback.
8. **How to optimize prompts automatically?** Use DSPy-style optimization with training data and metrics.
9. **Explain system message engineering.** Crafting role definitions that guide model behavior consistently.

### Architect Level
10. **Design multi-tenant prompt system.** Per-tenant customization + base templates + overrides + compliance + audit.
11. **How to handle prompt drift?** Monitor metrics, regression tests, automated alerts, periodic review.
12. **Explain prompt security concerns.** Injection attacks, sensitive data in templates, access control, audit logs.

## Examples

See `examples/` for runnable demos:
- Template loading and rendering
- Meta-prompt generation
- System message usage
- A/B testing setup

## References

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [DSPy: Programming with Foundation Models](https://github.com/stanfordnlp/dspy)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

---

*Production-ready template system with versioning and A/B testing.*
