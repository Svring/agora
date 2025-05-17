# Functional Python Style Guide for Project Agora

This document outlines the guiding principles and coding style for Python development in Project Agora, drawing heavily from the patterns established in `core/card_system/card_manager.py`. The core philosophy is to leverage functional programming paradigms, strong typing with Pydantic, and monadic patterns for robust and maintainable code.

## 1. Core Principles

*   **Immutability**: Data structures, once created, should not be changed. Modifications should result in new instances.
*   **Purity**: Functions should ideally be pure, meaning their output depends only on their input, and they have no side effects (or side effects are carefully managed and isolated).
*   **Explicitness**: Data flow and potential failure paths should be explicit, primarily through the use of monadic types.
*   **Type Safety**: Leverage Python's type hinting system and Pydantic's validation to catch errors early.
*   **Separation of Concerns**: Clearly separate data definitions (models) from behavior (functions).

## 2. Data Modeling with Pydantic

*   **Exclusive Use**: All custom data structures (representing state, configurations, errors, reports, etc.) **must** be defined as Pydantic `BaseModel`s.
*   **Immutability (`frozen=True`)**: All Pydantic models **must** be immutable. Achieve this by adding `class Config: frozen = True` to each model.
    ```python
    from pydantic import BaseModel

    class MyImmutableData(BaseModel):
        field_a: str
        field_b: int

        class Config:
            frozen = True
            arbitrary_types_allowed = True # If using complex types like Path
    ```
*   **Immutable Collections**:
    *   For sequences within Pydantic models that should not change after creation, use `Tuple` instead of `List`.
        *   Example: `errors: Tuple[ErrorType, ...]`
    *   For dictionaries, while the `dict` type itself is mutable, all operations that "modify" a dictionary within a frozen Pydantic model context **must** create a new dictionary and update the model by creating a new model instance via `model_copy(update=...)`.
*   **Strict Typing**: All model fields **must** have explicit type hints using the `typing` module. Prefer specific types (e.g., `Tuple[str, ...]`) over general ones (e.g., `tuple`).
*   **Default Factories**: Use `Field(default_factory=tuple)` or `Field(default_factory=dict)` for fields that are collections and should default to an empty immutable collection.
*   **Configuration**: `arbitrary_types_allowed = True` in `Config` can be used if Pydantic needs to accommodate types it doesn't natively understand well (e.g., `pathlib.Path`), but use judiciously.

## 3. Functional Programming & Control Flow

*   **Pure Functions**:
    *   Strive to write functions whose output is solely determined by their inputs, without side effects.
    *   When a function needs to "change" data (especially immutable Pydantic models), it **must** return a *new instance* of that data with the changes applied.
    *   Use Pydantic's `model_copy(update={...})` method for creating modified instances of models.
        ```python
        def update_report_error(report: CardLoadingReport, error: CardLoadingError) -> CardLoadingReport:
            new_errors = report.errors + (error,)
            return report.model_copy(update={"errors": new_errors, "error_count": report.error_count + 1})
        ```
*   **`returns` Library for Monadic Control Flow**:
    *   The `returns` library is central to managing operations that can succeed or fail, and for handling optional values.
    *   **`Result[SuccessType, FailureType]`**: Functions that can fail (e.g., I/O, parsing, validation) **must** return a `Result`.
        *   `Success(value)` indicates a successful operation.
        *   `Failure(error_value)` indicates a failure.
    *   **`Maybe[ValueType]`**: Use `Maybe.from_optional(...)` for values that might be absent.
    *   **Chaining Operations**:
        *   Use `.bind(callable)` to sequence operations where `callable` takes the unwrapped success value and returns a new `Result`.
        *   Use `.map(callable)` to transform the success value of a `Result` without changing its context (i.e., `callable` returns a plain value, `map` re-wraps it in `Success`).
        *   Use `.alt(callable)` to transform the failure value of a `Result` (i.e., `callable` takes the error, performs an action, and typically returns a new `Result`, often a `Success` to indicate recovery or a new `Failure`).
        *   Use `.lash(callable)` to perform a side-effect on a `Failure` and propagate the original `Failure`. The callable should return the original `Failure` or a new one.
        *   Avoid manual `isinstance(res, Success)` checks where chaining can be used.
    *   **Unwrapping**:
        *   Only use `.unwrap()` when the preceding chain guarantees a `Success` (e.g., after an `.alt()` that handles all possible failure types and transforms them into `Success`).
        *   For `Maybe`, use methods like `.map()`, `.unwrap_or(default)`, `.value_or(default)` or pattern matching.
*   **`functools.reduce` for Iterative Accumulation**:
    *   When processing a collection of items to produce an accumulated result (especially with immutable state updates), prefer `functools.reduce`.
    *   The reducing function must be pure, taking the accumulator and the current item, and returning the new accumulator.
*   **Avoid Side Effects in Core Logic**: Functions involved in data transformation or decision-making should avoid direct side effects (printing, file I/O). Isolate side effects to the "edges" of the system or specific utility functions that clearly indicate their nature (and often wrap them in `Result`).

## 4. Error Handling

*   **Custom Error Types**: Define specific Pydantic models for different error conditions to carry semantic information.
*   **Union Types for Errors**: Use `typing.Union` to create composite error types that a `Result` can fail with.
*   **Propagation**: Errors should be propagated via the `Failure` path of `Result` objects.
*   **Reporting**: Accumulate errors in dedicated report models (like `CardLoadingReport`), ensuring the accumulation process itself is immutable.

## 5. Type Annotations

*   All function parameters and return types **must** be fully type-annotated using Python's `typing` module.
*   Variables should also be type-annotated where it enhances clarity, especially for complex types.

## 6. Structure and Modularity

*   **File Organization**:
    1.  Imports.
    2.  Pydantic Model Definitions (Errors, Data/State, Reports).
    3.  Core Functional Logic (helper functions often prefixed with `_`, pure functions ideally named to reflect this).
    4.  Public API Functions.
    5.  Example Usage / Test Block (`if __name__ == "__main__":`).
*   **Small, Focused Functions**: Break down complex logic into smaller, manageable, and testable functions.

## 7. Python Features

*   Utilize modern Python features (Python 3.10+ assumed).
    *   **`match` statement**: Preferred for complex conditional logic based on data structure variants or types (especially with Pydantic models and `Result` objects).
*   **Standard Library**: Leverage `pathlib` for path manipulations, `functools` for functional tools.

## 8. Dependencies Management

*   Key libraries for this style:
    *   `pydantic`: For data validation, serialization, and immutable model definition.
    *   `returns`: For monadic programming (`Result`, `Maybe`, railway-oriented programming).
    *   `PyYAML` (or similar): For specific I/O tasks, with interactions wrapped in `Result`-returning functions.

## Example Snippet (Illustrating Chaining and Immutability)

```python
from returns.result import Result, Success, Failure
from functools import reduce

# Assume State and Report are frozen Pydantic models
# Assume process_item returns Result[NewState, Error]

def process_item_for_fold(
    accumulator: Tuple[State, Report],
    item: ItemToProcess
) -> Tuple[State, Report]:
    current_state, current_report = accumulator

    def handle_success(processed_value: ProcessedValue) -> Tuple[State, Report]:
        # Returns new state and report
        return update_state_with_success(current_state, current_report, processed_value)

    def handle_failure(error: ItemError) -> Result[Tuple[State, Report], Any]:
        # Returns Success with current state and updated report
        return Success((current_state, update_report_with_error(current_report, error)))

    return (
        parse_item(item) # -> Result[ParsedItem, ParseItemError]
        .bind(lambda parsed: validate_item(parsed, current_state)) # -> Result[ValidatedItem, ValidationError]
        .map(handle_success) # -> Result[Tuple[State, Report], Error]
        .alt(handle_failure) # -> Result[Tuple[State, Report], Any] # Error type from alt is nominal
        .unwrap() # Assumes .alt always converts to Success
    )

# Initial state and report are created before the fold
# final_state, final_report = reduce(process_item_for_fold, item_list, (initial_state, initial_report))
```

This style guide aims to produce a codebase that is robust, easier to reason about due to immutability and explicit data flow, and more maintainable in the long run. 