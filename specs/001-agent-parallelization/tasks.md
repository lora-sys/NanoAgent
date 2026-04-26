# Tasks: Agent Parallelization Module

**Input**: Design documents from `/specs/001-agent-parallelization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Yes - unit and integration tests using AgentTestHarness framework

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create executor module structure

- [x] T001 Create `core/executor/` directory structure
- [x] T002 [P] Create `core/executor/__init__.py` with module exports

---

## Phase 2: Foundational (Core Data Model - Blocking Prerequisites)

**Purpose**: Core classes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `core/executor/result.py` with ExecutionResult and ExecutionStatus dataclasses per data-model.md
- [x] T004 Create `core/executor/graph.py` with TaskNode, Condition, and ExecutionGraph classes per data-model.md

**Checkpoint**: Core data model ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Parallel Task Execution (Priority: P1) 🎯 MVP

**Goal**: Enable parallel execution of independent tasks using asyncio.gather

**Independent Test**: Submit 3 independent file search tasks, verify parallel execution (total time ≈ longest task, not sum)

### Tests for User Story 1

> Write tests FIRST, ensure they FAIL before implementation

- [x] T005 [P] [US1] Unit test for ParallelExecutor in `tests/test_executor.py::test_parallel_execution_timing`
- [x] T006 [P] [US1] Integration test for parallel task completion in `tests/test_executor.py::test_parallel_all_complete`

### Implementation for User Story 1

- [x] T007 Create `core/executor/executor.py` with ParallelExecutor class using asyncio.gather
- [x] T008 [P] [US1] Add max_concurrency parameter to ParallelExecutor
- [x] T009 [P] [US1] Implement task status tracking (pending→running→completed/failed)
- [x] T010 [US1] Implement error_strategy: stop, fail-fast, continue
- [x] T011 [US1] Add timeout handling per TaskNode

**Checkpoint**: US1 functional - 3 independent tasks execute in parallel

---

## Phase 4: User Story 2 - Sequential Chain Composition (Priority: P1)

**Goal**: Extend PromptChain to support sequential execution with context propagation

**Independent Test**: Define 3-step chain, verify step2 uses step1 output, step3 uses step2 output

### Tests for User Story 2

- [x] T012 [P] [US2] Unit test for SerialExecutor in `tests/test_executor.py::test_serial_execution`
- [x] T013 [P] [US2] Integration test for chain context propagation in `tests/test_executor.py::test_chain_context_propagation`

### Implementation for User Story 2

- [x] T014 Create SerialExecutor class in `core/executor/executor.py`
- [x] T015 [P] [US2] Implement context passing between sequential steps
- [x] T016 [US2] Implement stop_on_error behavior matching existing PromptChain
- [ ] T017 [US2] Modify `core/chain.py` to use SerialExecutor internally

**Checkpoint**: US2 functional - sequential chain with proper context flow

---

## Phase 5: User Story 3 - Conditional Control Flow (Priority: P2)

**Goal**: Support if/else branching based on task execution results

**Independent Test**: Define condition "if result contains 'error' then path_A else path_B", verify correct path selection

### Tests for User Story 3

- [x] T018 [P] [US3] Unit test for condition evaluation in `tests/test_executor.py::test_condition_evaluation`
- [x] T019 [P] [US3] Integration test for conditional branching in `tests/test_executor.py::test_conditional_branch_taken`

### Implementation for User Story 3

- [x] T020 Create `core/executor/conditions.py` with expression parser
- [x] T021 [P] [US3] Implement eval_condition function supporting `result.contains()`, `result.get()`, comparisons
- [x] T022 [P] [US3] Implement Condition class with then_node/else_node
- [x] T023 [US3] Implement FlowController to handle branching logic
- [x] T024 [US3] Add default branch handling for invalid expressions

**Checkpoint**: US3 functional - conditional branching selects correct path

---

## Phase 6: User Story 4 - Integration with Agent/Chain/Router (Priority: P2)

**Goal**: Seamless integration with existing NanoAgent architecture

**Independent Test**: Configure NanoAgent with ParallelExecutor, verify Router subtasks execute in parallel

### Tests for User Story 4

- [x] T025 [P] [US4] Integration test for executor integration in `tests/test_executor.py::test_executor_with_agent`
- [x] T026 [P] [US4] Integration test for Router output to executor in `tests/test_executor.py::test_router_to_executor`

### Implementation for User Story 4

- [x] T027 [P] [US4] Add executor parameter to NanoAgent.__init__ in `core/agent.py`
- [x] T028 [P] [US4] Modify agent execution loop to use ParallelExecutor when configured
- [x] T029 [US2] Create executor_demo usage example in `examples/executor_demo/demo.py`

**Checkpoint**: US4 functional - executor integrated into agent execution loop

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements across all user stories

- [x] T030 [P] Add DAG cycle detection to prevent circular dependencies
- [x] T031 [P] Add partial results handling when execution interrupted
- [x] T032 [P] Update CLAUDE.md to document new executor module
- [x] T033 [P] Run full test suite: `uv run pytest tests/test_executor.py -v`
- [x] T034 Run quickstart.md validation with demo.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational completion
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 - No dependencies on other stories
- **US2 (P1)**: Depends on Phase 2 - No dependencies on US1 (can run parallel)
- **US3 (P2)**: Depends on Phase 2 - Can run parallel with US1/US2
- **US4 (P2)**: Depends on US2 completion (chain integration)

### Within Each User Story

- Tests (TDD): Write and FAIL before implementation
- Foundational classes before executor logic
- Serial executor before conditional (US3 depends on US2 context)
- Integration last within each story

### Parallel Opportunities

- T001-T002 can run in parallel
- T005-T006, T012-T013, T018-T019, T025-T026 can run in parallel (all different test files)
- T008-T009 can run in parallel
- T021-T022 can run in parallel
- T027-T028 can run in parallel

---

## Parallel Example: Foundational → US1

```bash
# Phase 2 (foundational) - sequential due to dependencies
Task: T003 Create ExecutionResult dataclass
Task: T004 Create TaskNode, Condition, ExecutionGraph (depends on T003)

# Phase 3 (US1) - parallel opportunities within
Task: T005 Write test_parallel_execution_timing (FAILS)
Task: T006 Write test_parallel_all_complete (FAILS)
# ... then implement ...
Task: T007 Create ParallelExecutor
Task: T008 Add max_concurrency parameter
Task: T009 Add task status tracking
```

---

## Implementation Strategy

### MVP First (US1 Parallel Execution Only)

1. Phase 1-2: Setup + Foundational
2. Phase 3: US1 Parallel Execution
3. **STOP and VALIDATE**: Test parallel timing works
4. Deploy/demo if ready

### Full Feature Set

1. Phase 1-2: Setup + Foundational
2. Phase 3: US1 Parallel Execution → Test → Demo
3. Phase 4: US2 Sequential Chain → Test → Demo
4. Phase 5: US3 Conditional Branching → Test → Demo
5. Phase 6: US4 Integration → Test → Demo
6. Phase 7: Polish & Validate

---

## Notes

- [P] tasks = different files, no dependencies - safe for parallel execution
- [Story] label = traceability to spec user stories
- Each user story independently testable via `uv run pytest tests/test_executor.py::test_[story]`
- Commit after each phase completion
- Stop at checkpoints to validate independently
