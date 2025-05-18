# Event definitions and dispatcher
# from typing import Callable, Dict, List, Any

# class Event:
#     """Base class for events."""
#     pass

# # Example specific event
# class PlayerActionEvent(Event):
#     def __init__(self, player_id: str, action: str, details: Dict[str, Any]):
#         self.player_id = player_id
#         self.action = action
#         self.details = details

# class EventDispatcher:
#     def __init__(self):
#         self._listeners: Dict[type[Event], List[Callable[[Event], None]]] = {}

#     defsubscribe(self, event_type: type[Event], listener: Callable[[Event], None]):
#         if event_type not in self._listeners:
#             self._listeners[event_type] = []
#         self._listeners[event_type].append(listener)

#     defdispatch(self, event: Event):
#         if type(event) in self._listeners:
#             for listener in self._listeners[type(event)]:
#                 listener(event)
