from typing import Callable, Dict, Any, Type
from pydantic import Field
from returns.result import Result, Success, Failure, safe

from .event_models import GameEvent, ListenerRegistry, SystemEventType


# Pure Function to create an empty ListenerRegistry
def create_listener_registry() -> ListenerRegistry[GameEvent]:
    """
    Creates and returns a new, empty ListenerRegistry instance.
    Returns:
        ListenerRegistry[GameEvent]: A new listener registry.
    """
    return ListenerRegistry[GameEvent](listeners={})


# Pure Function to Subscribe a Listener
def subscribe_listener(
    registry: ListenerRegistry[GameEvent],
    event_name: SystemEventType,
    listener: Callable[[GameEvent], None],
) -> ListenerRegistry[GameEvent]:
    """
    Subscribes a listener to a specific event type (by enum member), returning a new ListenerRegistry instance.
    The original registry remains unchanged.
    Args:
        registry: The current ListenerRegistry instance.
        event_name: The SystemEventType enum member to listen for.
        listener: A callable that takes an instance of GameEvent as its argument.
    Returns:
        ListenerRegistry[GameEvent]: A new ListenerRegistry instance with the listener added.
    """
    current_listeners_for_type = registry.listeners.get(event_name, tuple())
    new_listeners_for_type_tuple = current_listeners_for_type + (listener,)

    updated_listeners_dict = {
        **registry.listeners,
        event_name: new_listeners_for_type_tuple,
    }

    return registry.model_copy(update={"listeners": updated_listeners_dict})


# Pure Function to Dispatch an Event
def dispatch_event(
    registry: ListenerRegistry[GameEvent], event: GameEvent
) -> Result[None, str]:
    """
    Dispatches an event to all relevant listeners in the registry.
    Listener execution is wrapped to catch exceptions, allowing other listeners to run.
    Args:
        registry: The ListenerRegistry containing subscriptions.
        event: The GameEvent instance to dispatch.
    Returns:
        Result[None, str]: Success(None) if all listeners executed without error,
                           Failure(str) with aggregated error messages otherwise.
    """

    @safe
    def execute_listener_safely(
        listener: Callable[[GameEvent], None], event_to_dispatch: GameEvent
    ) -> None:
        listener(event_to_dispatch)
        return None

    listeners_for_event_type = registry.listeners.get(event.event_name, tuple())

    unique_listeners_to_call = list(dict.fromkeys(listeners_for_event_type))

    results: list[Result[None, Exception]] = []
    for listener_func in unique_listeners_to_call:
        result = execute_listener_safely(listener_func, event)
        results.append(result)

    failures = [res for res in results if isinstance(res, Failure)]
    if failures:
        error_messages = [str(f.failure()) for f in failures]
        return Failure(
            f"Dispatch failed for event {event.event_id} (type: {event.event_name}). Errors: {'; '.join(error_messages)}"
        )

    return Success(None)


__all__ = [
    "create_listener_registry",
    "subscribe_listener",
    "dispatch_event",
    "ListenerRegistry",
    "GameEvent",
    "SystemEventType",
]

if __name__ == "__main__":

    listener_call_counts: Dict[str, int] = {}
    received_event_data: Dict[str, list[Any]] = {}

    def reset_test_trackers():
        global listener_call_counts, received_event_data
        listener_call_counts = {
            "log_event_listener": 0,
            "test_event_listener": 0,
            "another_event_listener": 0,
            "failing_listener": 0,
            "specific_error_event_listener": 0,
        }
        received_event_data = {
            "log_event_listener": [],
            "test_event_listener": [],
            "another_event_listener": [],
            "failing_listener": [],
            "specific_error_event_listener": [],
        }

    def log_event_listener(event: GameEvent):
        listener_call_counts["log_event_listener"] += 1
        received_event_data["log_event_listener"].append(event.event_name)
        print(
            f"LogListener: Event {event.event_id} type {event.event_name.value} from {event.source_module}"
        )

    def test_event_listener(event: GameEvent):
        if event.event_name == SystemEventType.TEST_EVENT:
            listener_call_counts["test_event_listener"] += 1
            received_event_data["test_event_listener"].append(
                event.payload.get("message")
            )
            print(f"TestEventListener: Received {event.payload.get('message')}")

    def another_event_listener(event: GameEvent):
        if event.event_name == SystemEventType.PLAYER_EVENT:
            listener_call_counts["another_event_listener"] += 1
            received_event_data["another_event_listener"].append(
                event.payload.get("value")
            )
            print(
                f"AnotherEventListener: Received value {event.payload.get('value')} for a PLAYER_EVENT"
            )

    def failing_listener(event: GameEvent):
        listener_call_counts["failing_listener"] += 1
        print(
            f"FailingListener: About to fail for event {event.event_id} (type: {event.event_name})"
        )
        raise ValueError("Intentional failure in listener")

    def specific_error_event_listener(event: GameEvent):
        if event.event_name == SystemEventType.SPECIFIC_ERROR_TEST_EVENT:
            listener_call_counts["specific_error_event_listener"] += 1
            received_event_data["specific_error_event_listener"].append(
                event.payload.get("error_code")
            )
            print(
                f"SpecificErrorListener: Received error code {event.payload.get('error_code')}"
            )

    print("\n--- Running Event Provider Tests (Enum-Based Events) ---")

    def test_registry_creation_and_initial_state():
        print("Test: test_registry_creation_and_initial_state")
        reset_test_trackers()
        registry = create_listener_registry()
        assert isinstance(registry, ListenerRegistry)
        assert registry.listeners == {}
        print("PASS: test_registry_creation_and_initial_state")

    test_registry_creation_and_initial_state()

    def test_subscribe_listener_immutability_and_structure():
        print("Test: test_subscribe_listener_immutability_and_structure")
        reset_test_trackers()
        registry1: ListenerRegistry[GameEvent] = create_listener_registry()
        registry2 = subscribe_listener(
            registry1, SystemEventType.GENERAL_EVENT, log_event_listener
        )
        assert registry1 is not registry2
        assert registry1.listeners == {}
        assert (
            SystemEventType.GENERAL_EVENT in registry2.listeners
            and len(registry2.listeners[SystemEventType.GENERAL_EVENT]) == 1
        )

        registry3 = subscribe_listener(
            registry2, SystemEventType.TEST_EVENT, test_event_listener
        )
        assert (
            SystemEventType.TEST_EVENT in registry3.listeners
            and len(registry3.listeners[SystemEventType.TEST_EVENT]) == 1
        )
        assert SystemEventType.GENERAL_EVENT in registry3.listeners
        print("PASS: test_subscribe_listener_immutability_and_structure")

    test_subscribe_listener_immutability_and_structure()

    def test_dispatch_simple_success():
        print("Test: test_dispatch_simple_success")
        reset_test_trackers()
        registry: ListenerRegistry[GameEvent] = create_listener_registry()
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )

        event = GameEvent(
            event_name=SystemEventType.TEST_EVENT,
            source_module="TestDispatch",
            payload={"message": "Hello Success"},
        )
        result = dispatch_event(registry, event)

        assert isinstance(result, Success)
        assert listener_call_counts["test_event_listener"] == 1
        assert received_event_data["test_event_listener"][0] == "Hello Success"
        print("PASS: test_dispatch_simple_success")

    test_dispatch_simple_success()

    def test_dispatch_specific_event_types():
        print("Test: test_dispatch_specific_event_types")
        reset_test_trackers()
        registry: ListenerRegistry[GameEvent] = create_listener_registry()
        registry = subscribe_listener(
            registry, SystemEventType.GENERAL_EVENT, log_event_listener
        )
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )
        registry = subscribe_listener(
            registry,
            SystemEventType.SPECIFIC_ERROR_TEST_EVENT,
            specific_error_event_listener,
        )

        test_event = GameEvent(
            event_name=SystemEventType.TEST_EVENT,
            source_module="SpecificTest",
            payload={"message": "Specific Test Event"},
        )
        dispatch_event(registry, test_event)
        assert listener_call_counts["log_event_listener"] == 0
        assert listener_call_counts["test_event_listener"] == 1
        assert listener_call_counts["specific_error_event_listener"] == 0
        reset_test_trackers()

        error_event = GameEvent(
            event_name=SystemEventType.SPECIFIC_ERROR_TEST_EVENT,
            source_module="ErrorTest",
            payload={"message": "Error Event", "error_code": 500},
        )
        dispatch_event(registry, error_event)
        assert listener_call_counts["log_event_listener"] == 0
        assert listener_call_counts["test_event_listener"] == 0
        assert listener_call_counts["specific_error_event_listener"] == 1

        generic_event = GameEvent(
            event_name=SystemEventType.GENERAL_EVENT,
            source_module="GenericDispatch",
        )
        dispatch_event(registry, generic_event)
        assert listener_call_counts["log_event_listener"] == 1
        print("PASS: test_dispatch_specific_event_types")

    test_dispatch_specific_event_types()

    def test_dispatch_with_failing_listener():
        print("Test: test_dispatch_with_failing_listener")
        reset_test_trackers()
        registry: ListenerRegistry[GameEvent] = create_listener_registry()
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, failing_listener
        )
        registry = subscribe_listener(
            registry, SystemEventType.GENERAL_EVENT, log_event_listener
        )

        event = GameEvent(
            event_name=SystemEventType.TEST_EVENT,
            source_module="FailureTest",
            payload={"message": "Trigger Failure"},
        )
        result = dispatch_event(registry, event)

        assert isinstance(result, Failure)
        assert "Intentional failure in listener" in str(result.failure())
        assert listener_call_counts["test_event_listener"] == 1
        assert listener_call_counts["failing_listener"] == 1
        assert listener_call_counts["log_event_listener"] == 0
        print("PASS: test_dispatch_with_failing_listener")

    test_dispatch_with_failing_listener()

    def test_dispatch_no_relevant_listeners():
        print("Test: test_dispatch_no_relevant_listeners")
        reset_test_trackers()
        registry: ListenerRegistry[GameEvent] = create_listener_registry()
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )

        event_other_type = GameEvent(
            event_name=SystemEventType.PLAYER_EVENT,
            source_module="OtherTypeTest",
            payload={"value": 99},
        )
        result = dispatch_event(registry, event_other_type)
        assert isinstance(result, Success)
        assert listener_call_counts["test_event_listener"] == 0
        print("PASS: test_dispatch_no_relevant_listeners")

    test_dispatch_no_relevant_listeners()

    def test_listener_uniqueness_per_dispatch():
        print("Test: test_listener_uniqueness_per_dispatch")
        reset_test_trackers()
        registry: ListenerRegistry[GameEvent] = create_listener_registry()

        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )
        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )

        registry = subscribe_listener(
            registry, SystemEventType.TEST_EVENT, test_event_listener
        )

        event = GameEvent(
            event_name=SystemEventType.TEST_EVENT,
            source_module="DedupeTest",
            payload={"message": "Dedupe Check"},
        )
        result = dispatch_event(registry, event)
        assert isinstance(result, Success)
        assert listener_call_counts["test_event_listener"] == 1
        assert received_event_data["test_event_listener"][0] == "Dedupe Check"
        print("PASS: test_listener_uniqueness_per_dispatch")

    test_listener_uniqueness_per_dispatch()

    print("--- Event Provider Tests (Enum-Based Events) Complete ---\n")
