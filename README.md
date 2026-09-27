# 🥬 VeggieOps AI

> An AI-powered backend system for vegetable resale businesses — from farm to profit, tracked end-to-end.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-Milestone%201-orange.svg)]()
[![Local AI](https://img.shields.io/badge/AI-100%25%20Local-brightgreen.svg)]()

---

## The Problem

Vegetable shop owners buy produce in large lots, but most **cannot answer** the most important business question:

> *"How much money did I really make on Lot L001 — once I count fuel, labor, spoilage, and packaging?"*

Costs are scattered across trips, deliveries, sorting, grading, storage, and waste. Without a unified system, profit is a guess.

## The Solution

VeggieOps AI tracks every vegetable lot from acquisition to final sale, computes the **true cost and profit**, predicts future performance, and answers business questions in plain English through a self-hosted AI agent.

## ✨ Features

- 🌱 **Lot Lifecycle Tracking** — Farm → Collection → Registration → Sorting → Grading → Inventory → Sale
- 💰 **True Cost Engine** — Allocate acquisition, transport, processing, storage, and waste costs across items using configurable rules
- 🏷️ **Quality Grading** — A, A-, B, B-, C, C-, RECYCLE hierarchy with full test history
- 📦 **Flexible Units** — Per kilogram, per piece, per half, per quarter, custom units
- 📊 **Analytics Dashboard** — Operations, finance, quality, inventory, forecasting views
- 🔮 **Forecasting** — Predict sales, revenue, profit, waste, and demand using historical data
- 🤖 **Three-Model AI Agent** — Self-hosted LLM agent with intelligent model routing (small router → general reasoner → advanced analyst)
- 🔧 **Tool-Based AI** — The agent calls real backend functions instead of hallucinating numbers
- 💸 **100% Local** — No cloud AI bills, no data leaves your machine

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Next.js) — Dashboard + AI Chat      │
└──────────────────┬──────────────────────────────┘
                   │ REST
┌──────────────────▼──────────────────────────────┐
│  Backend (FastAPI) — Business Logic + AI       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────┐ │
│  │ Cost Engine  │  │ AI Agent     │  │ ML    │ │
│  │ Inventory    │  │ + Router     │  │ Fore- │ │
│  │ Pricing      │  │              │  │ cast  │ │
│  └──────────────┘  └──────┬───────┘  └───────┘ │
└─────────────────────────────┼───────────────────┘
                              │ HTTP
┌─────────────────────────────▼───────────────────┐
│  Ollama (Local AI Runtime)                      │
│  • Model 1: qwen2.5-coder:1.5b (Router)         │
│  • Model 2: gemma3:4b (General Reasoning)       │
│  • Model 3: qwen2.5:7b (Advanced Analysis)      │
└─────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────┐
│  PostgreSQL (Local Docker Container)            │
└─────────────────────────────────────────────────┘
```

See [`architecture.md`](./architecture.md) for the full design.

## 🚀 Quick Start

> **Prerequisites**: Docker Desktop, Git, Ollama running with models pulled, NVIDIA GPU recommended

```powershell
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/vegetable-ai.git
cd vegetable-ai

# 2. Copy environment template (filled in later milestones)
cp .env.example .env

# 3. Start backend services (Postgres + FastAPI + Dashboard)
docker compose up -d

# 4. Open the dashboard
# http://localhost:3000
```

Detailed setup coming in Milestone 2.

## 📁 Project Structure

```
vegetable-ai/
├── backend/          # FastAPI application (Milestone 2+)
├── frontend/         # Next.js dashboard (Milestone 10+)
├── agent/            # AI agent logic (Milestone 12+)
├── ml/               # ML forecasting models (Milestone 11+)
├── data/             # Synthetic and real datasets
├── database/         # SQLAlchemy models + Alembic migrations
├── infra/            # Docker Compose, deployment configs
├── scripts/          # Utility scripts
├── tests/            # Test suites
├── docs/             # Documentation
│   ├── adr/          # Architecture Decision Records
│   └── diagrams/     # Mermaid source files
├── architecture.md   # System architecture overview
├── README.md         # You are here
└── LICENSE           # MIT license
```

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Python 3.11+, FastAPI | Modern, typed, async-ready |
| Database | PostgreSQL 15 | Relational integrity for lots/items/sales |
| ORM | SQLAlchemy 2.x, Alembic | Industry standard, type-safe migrations |
| AI Models | Ollama + Qwen/Gemma | Self-hosted, private, free |
| AI Routing | Custom (in FastAPI) | Transparent, learnable, no abstractions |
| ML | scikit-learn, Prophet | Production-proven, beginner-friendly |
| Frontend | Next.js 14, TypeScript, Tailwind, Recharts | Modern React stack |
| Container | Docker + Docker Compose | Local dev = production |
| Validation | Pydantic v2 | Type-safe request/response |

## 🗺️ Roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Business requirements & architecture docs | ✅ In progress |
| 2 | Local dev environment (Docker Compose) | ⏳ Next |
| 3 | Database schema (incl. Purchase Orders) | ⏳ Planned |
| 4 | Synthetic dataset generator | ⏳ Planned |
| 5 | Backend CRUD APIs | ⏳ Planned |
| 6 | Lot processing workflow | ⏳ Planned |
| 7 | Inventory system | ⏳ Planned |
| 8 | Cost calculation engine | ⏳ Planned |
| 9 | Sales system | ⏳ Planned |
| 10 | Analytics dashboard | ⏳ Planned |
| 11 | Forecasting models | ⏳ Planned |
| 12 | Three-model AI architecture | ⏳ Planned |
| 13 | AI tool calling | ⏳ Planned |
| 14 | RAG for business rules | ⏳ Planned |
| 15 | Evaluation framework | ⏳ Planned |
| 16 | Production hardening | ⏳ Planned |

See [`docs/roadmap.md`](./docs/roadmap.md) for the full 22-milestone plan.

## 🤖 The Three-Model AI Agent

VeggieOps AI uses **three locally-hosted models** with distinct roles:

| Role | Model | Job |
|---|---|---|
| **Router** (Model 1) | `qwen2.5-coder:1.5b` | Classify intent, extract structured data, ~100ms response |
| **General** (Model 2) | `gemma3:4b` | Business reasoning, explanations, most queries |
| **Advanced** (Model 3) | `qwen2.5:7b` | Complex multi-step analysis, anomaly investigation |

The **router** decides which model handles each query. Simple questions stay cheap and fast. Hard questions escalate to the advanced model.

**The agent never hallucinates financial numbers.** All money math goes through deterministic backend services that the agent calls as tools.

## 🔒 Privacy & Cost

- ✅ **No cloud AI services** — all inference runs locally via Ollama
- ✅ **No data leaves your machine** — Postgres + AI + code all on your hardware
- ✅ **No subscription fees** — completely free forever after setup
- ⚠️ **Hardware requirement** — NVIDIA GPU with 8GB+ VRAM recommended (RTX 3080 or better)

## 📚 Documentation

- [Architecture Overview](./architecture.md)
- [Architecture Decision Records](./docs/adr/)
- [Glossary](./docs/glossary.md)
- [Roadmap](./docs/roadmap.md)

## 🤝 Contributing

This is a learning project. Suggestions, bug reports, and educational contributions are welcome via GitHub issues.

## 📄 License

[MIT](./LICENSE) — free to use, modify, and distribute.

---

**Built as a serious capstone project for learning AI engineering from first principles.**
