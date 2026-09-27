# ADR-0003: Use Local AI Models via Ollama

**Status:** Accepted
**Date:** 2024-03-15
**Deciders:** VeggieOps AI Contributors

## Context

VeggieOps AI includes an intelligent agent that must answer natural language questions about the business. The agent needs access to large language models (LLMs).

We considered four deployment strategies:

1. **Cloud LLM APIs** (OpenAI, Anthropic, Google) — pay per token, data leaves the machine
2. **AWS Bedrock** — managed service with pay-per-use pricing
3. **Self-hosted open-source models** (Llama, Qwen, Mistral, Gemma) on our own hardware
4. **Hybrid** — local models for most work, cloud fallback for hardest queries

Constraints:

- The project operates on a **zero-cloud budget** (no AWS credits available).
- The developer has an **NVIDIA RTX 3080 (10GB VRAM)** workstation.
- **Business data privacy** is important: queries may contain farmer names, costs, and customer details.
- The project is a **learning exercise**: we want to understand the full AI stack, not consume black-box APIs.

## Decision

We will run **open-source LLMs locally via Ollama** for 100% of AI inference. No cloud LLM APIs will be used.

Our model roster:

| Role | Model | Parameters | Quantization | Approx VRAM |
|---|---|---|---|---|
| Router (Model 1) | `qwen2.5-coder:1.5b` | 1.5B | Q4 | ~1.5 GB |
| General (Model 2) | `gemma3:4b` | 4B | Q4 | ~3.3 GB |
| Advanced (Model 3) | `qwen2.5:7b` | 7B | Q4 | ~4.7 GB |

Total disk usage: ~9.3 GB. Worst-case VRAM (Router + Advanced loaded): ~6.2 GB, well within 10 GB.

## Consequences

### Easier

- **Zero ongoing AI cost.** No token bills; electricity only.
- **Full data privacy.** Business data never leaves the workstation.
- **Offline operation.** The system works without internet (after model download).
- **Learning value.** We control every layer of the AI stack — routing, prompting, tool calling, evaluation.
- **Fast iteration.** No API rate limits; we can run thousands of test queries during development.

### Harder

- **Hardware dependency.** Requires an NVIDIA GPU with 8GB+ VRAM minimum.
- **Model capability ceiling.** Open 7B models are less capable than frontier models (GPT-4 class) on the hardest reasoning tasks.
- **Operational responsibility.** We monitor VRAM, temperature, model loading, and version compatibility ourselves.
- **Model selection churn.** The "best" 7B model changes every few months; we must re-evaluate periodically.
- **Context length limits.** Smaller models often have shorter context windows (8K–32K tokens), which may limit complex multi-document RAG.

### Mitigations

- The **router architecture** ensures simple queries stay on the cheap, fast model, reducing latency.
- We **verify capabilities** of each chosen model against our actual tasks before committing.
- **Evaluation framework** (Milestone 15) lets us detect when a model underperforms and swap it out.
- A **hybrid escape hatch** is documented but not implemented: if a query genuinely requires frontier capability, we can add a cloud fallback for that specific case later.

## Alternatives Considered

### Cloud LLMs (OpenAI, Anthropic, Google)

**Rejected because**: Ongoing token costs; data privacy concerns; defeats the learning goal of understanding the full stack.

### AWS Bedrock

**Rejected because**: Originally planned, but the developer does not have AWS credits. The architecture is designed so that swapping in Bedrock later would be a single-file change in the inference client.

### Larger local models (30B, 70B)

**Rejected because**: Exceeds available VRAM. A 30B Q4 model needs ~18 GB; we have 10 GB. Even if we could run it, inference would be slow on consumer hardware.

### Custom fine-tuned domain models

**Rejected because**: Requires labeled training data we don't have yet, plus training compute. Revisit after we have 6+ months of real business data.

## Notes

This decision is reconsidered if:

- The developer acquires AWS credits or a budget for cloud inference
- The business grows to require multi-user concurrent inference (local GPU becomes a bottleneck)
- Open-source models plateau and frontier models become necessary for business value
- Privacy requirements change (e.g., the business wants to query from a mobile device off-network)
