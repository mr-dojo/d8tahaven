# Context Substrate Documentation

This directory contains all planning, architectural, and reference documentation for the Context Substrate system.

## Documentation Structure

### 📐 Architecture (`/architecture`)
Core architectural decisions, system design, and technical specifications.

- **build-decisions.md** - Living document tracking all major architectural choices and their rationale
- Future: Component diagrams, deployment architecture, scaling plans

### 🎯 Features (`/features`)
Feature roadmap, implementation order, and acceptance criteria tracking.

- **roadmap.md** - Complete feature list organized by the five stages
- **acceptance-criteria-template.md** - Standard Gherkin template for new features

### 📊 Data Models (`/data-models`)
Database schemas, entity relationships, and data flow documentation.

- **schema-overview.md** - PostgreSQL table designs (relational + vector + graph)
- **entity-relationships.md** - How content items relate to each other
- Future: Sample queries, indexing strategies

### 🔌 API (`/api`)
API specifications, endpoint documentation, and integration guides.

- **endpoints-overview.md** - All HTTP endpoints organized by stage
- Future: OpenAPI/Swagger specs, authentication docs, rate limiting

### 📚 Reference (`/reference`)
Terminology, glossaries, and reference materials.

- **glossary.md** - Domain terminology and system concepts

## Document Lifecycle

All documents in this folder are **living documents**—they evolve as the system is built:

- ✅ **Planning Phase**: Created during architectural decisions
- 🔄 **Development Phase**: Updated as features are implemented
- 📦 **Production Phase**: Reflect actual system behavior

## Contributing to Docs

When adding or modifying features:
1. Update the roadmap with status changes
2. Add Gherkin acceptance criteria to `/tests/features/`
3. Update API docs if endpoints change
4. Add new terms to glossary as needed
5. Document significant decisions in `/architecture/` as ADRs

---

**Last Updated**: 2026-01-12
