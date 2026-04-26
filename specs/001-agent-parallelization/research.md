# Research: Agent Parallelization Module

**Feature**: Agent Parallelization Module
**Date**: 2026-04-25
**Spec**: [spec.md](./spec.md)

## Decisions

### D1: Asyncio as Parallelization Foundation

**Decision**: Use Python asyncio as the parallelization primitive
**Rationale**: NanoAgent already uses asyncio in chain.py, maintains compatibility with existing async code
**Alternatives considered**: Threading (higher overhead), multiprocessing (IPC complexity)

### D2: DAG-based Execution Graph

**Decision**: Model tasks as Directed Acyclic Graph (DAG)
**Rationale**: Natural representation for task dependencies; enables topological sort for serial execution order; parallel branches become obvious
**Alternatives considered**: Linear chain only (too restrictive), petri nets (over-engineered)

### D3: Condition Syntax Using Python-like Expressions

**Decision**: Conditions like `result.contains("error")` or `result.status == "success"`
**Rationale**: Familiar syntax, easy to parse, matches Python user base
**Alternatives considered**: DSL (adds parser complexity), JSON condition (verbose)

### D4: Three Error Strategies

**Decision**: Support `stop` (halt all), `fail-fast` (stop on first failure), `continue` (ignore failures)
**Rationale**: Covers common patterns; matches chain.py `stop_on_error` behavior
**Alternatives considered**: Only one strategy (too limiting), 5+ strategies (overcomplicated)

### D5: Extend PromptChain, Don't Replace

**Decision**: Add parallel/conditional capabilities to PromptChain as new step types
**Rationale**: Backwards compatible; existing code continues to work; natural extension
**Alternatives considered**: New ParallelChain class (duplication), modify ChainStep directly (violates single responsibility)

## Summary

All technical decisions made. No unknowns remain. Implementation ready to proceed with:
- asyncio.gather for parallel execution
- DAG with topological sort for dependency resolution
- Python-like condition expressions
- Three error strategies
- Extend PromptChain architecture
