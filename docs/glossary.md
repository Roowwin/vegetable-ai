# VeggieOps AI — Domain Glossary

This document defines the vocabulary used throughout the project. When writing code or documentation, use these exact terms.

---

## Business Concepts

### Lot
A quantity of vegetables acquired together from a single source. A lot has a unique **lot code** (e.g., `L-2024-00001`) and represents the central unit of analysis for cost and profit calculations.

### Skid (Pallet)
A wooden or plastic platform on which a portion of a lot is stored after arrival. A single lot may be split across multiple skids. Each skid has a **skid code** (e.g., `SK-001`).

### Asset (Item)
An individually tracked item within a lot. Used for items large enough to track individually (pumpkins, cabbages, watermelons). Loose items (tomatoes, leafy greens) stay at the lot level. Each asset has an **asset code** (e.g., `AST-00045`).

### Farmer
A supplier of vegetables. Distinguished from a "Farm" (a physical location) because one farmer may operate multiple farms.

### Supplier
Broader term than "farmer" — includes farmers, wholesalers, and market vendors. In this project, "farmer" and "supplier" are often used interchangeably, but `supplier` in code is the more general concept.

### Collection Trip
A trip made by the shop owner (or an employee) to a farm to pick up vegetables. Has costs: fuel, vehicle wear, driver time.

### Delivery
When the farmer brings vegetables directly to the shop. Has different costs than a collection trip (no fuel for the shop owner, but possibly a delivery fee).

### Purchase Order (PO)
A formal commitment to buy vegetables from a specific farmer, with expected quantities, prices, and delivery date. One PO can produce multiple Lots (via partial deliveries).

---

## Quality and Grading

### Grade
A letter code assigned to an asset after quality inspection. Currently defined grades:

| Code | Name | Description |
|---|---|---|
| `A` | Premium | Top quality, full price |
| `A-` | Premium Minus | Slight imperfections |
| `B` | Standard | Good quality, mid price |
| `B-` | Standard Minus | Visible but acceptable defects |
| `C` | Economy | Heavy defects, low price |
| `C-` | Economy Minus | Barely sellable |
| `RECYCLE` | Recycle | Not sellable as fresh; compost, animal feed, or waste |

The grade system is **configurable** — additional grades can be added without code changes.

### Quality Test
The act of inspecting an asset and recording measurements (size, color, firmness, defects). Each test produces a grade assignment.

### Sort
The initial separation of a lot into "sellable" and "damaged" before grading. A lot may have multiple sort results (e.g., 200 kg sellable, 30 kg damaged).

### Recycle
The disposition of an asset that cannot be sold. Recycled items may still have recovery value (compost sale, animal feed) or may be pure waste.

---

## Units and Pricing

### Unit Type
The way a vegetable is sold. Supported unit types:

- `kg` — sold by weight (tomatoes, beans)
- `piece` — sold as a whole item (1 pumpkin)
- `half` — sold as ½ item (½ cabbage)
- `quarter` — sold as ¼ item (¼ cabbage)
- `custom` — business-defined unit (e.g., "bunch", "crate")

### Price Book
A table of (`vegetable`, `grade`, `unit_type`, `unit_price`, `effective_date`) that defines how much to charge. Multiple price rows can exist for the same item with different effective dates (price history).

---

## Cost and Profit

### Acquisition Cost
What we paid to obtain the lot. Includes the purchase price paid to the farmer.

### Processing Cost
Costs incurred after the lot arrives but before sale: sorting labor, grading labor, equipment use, electricity, packaging.

### Storage Cost
Cost of keeping the lot in inventory: cold room electricity, days × rate.

### Selling Cost
Costs incurred during sale: shop labor, packaging, delivery to customer, payment processing fees.

### Waste Cost
The lost value of recycled items. Computed as `acquisition_cost_per_kg × recycled_kg` minus any recovery revenue.

### Allocation Method
How a shared cost (e.g., trip fuel) is distributed across the assets in a lot. Methods: fixed, weight-based, count-based, time-based, volume-based.

### Profit Margin
`NetProfit / Revenue × 100`. Expressed as a percentage.

---

## AI Agent Concepts

### Intent
The category of a user query (e.g., "sales_query", "cost_query", "forecast_query"). Determined by the router.

### Tool
A backend function the AI agent can invoke (e.g., `analyze_supplier`, `calculate_lot_profit`). Tools are the **only** way the agent accesses business data.

### Router
The component that decides which AI model handles each query. Uses cheap heuristics first, then Model 1, before escalating to Model 2 or Model 3.

### RAG (Retrieval-Augmented Generation)
The pattern of retrieving relevant documents (SOPs, business rules) before generating a response. Used for queries that need domain knowledge not in the database.

### Audit Log
The persistent record of every AI query, model used, tools called, and result. Essential for debugging, cost tracking, and compliance.

---

## Technical Concepts

### Monorepo
A single Git repository containing all project components (backend, frontend, agent, ml, infra). See `docs/adr/0001-monorepo.md`.

### ORM (Object-Relational Mapper)
A library that maps database tables to Python classes. We use SQLAlchemy.

### Migration
A versioned change to the database schema, managed by Alembic. Migrations are checked into Git.

### Synthetic Data
Artificially generated data that mimics real business data, used for development and testing before real data exists. Clearly labeled as synthetic in the project.

### Spot Instance
Originally: an AWS concept for cheap, interruptible compute. **Not applicable** in our local-first architecture. We use the developer's local GPU instead.
