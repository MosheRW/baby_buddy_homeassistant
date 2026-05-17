"""Platform for babybuddy sensor integration."""

from __future__ import annotations

from homeassistant.const import ATTR_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_TIMERS, SENSOR_TYPES
from .coordinator import BabyBuddyConfigEntry, BabyBuddyCoordinator
from .entity import BabyBuddyChildDataSensor, BabyBuddyChildSensor, BabyBuddyTimerSensor


# For a platform to support config entries, it will need to add a setup entry function
async def async_setup_entry(
    hass: HomeAssistant,
    entry: BabyBuddyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the babybuddy sensors."""
    coordinator = entry.runtime_data.coordinator
    tracked: dict = {}

    @callback
    def update_entities() -> None:
        """Update entities."""
        update_items(coordinator, tracked, async_add_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))

    update_entities()


@callback
def update_items(
    coordinator: BabyBuddyCoordinator,
    tracked: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add new sensors for new endpoint entries."""
    if coordinator.data is not None:
        new_entities = []
        for child in coordinator.data[0]:
            child_id = child[ATTR_ID]
            if child_id not in tracked:
                tracked[child_id] = BabyBuddyChildSensor(coordinator, child)
                new_entities.append(tracked[child_id])
            for description in SENSOR_TYPES:
                key = f"{child_id}_{description.key}"
                if coordinator.data[1][child_id].get(description.key) and key not in tracked:
                    tracked[key] = BabyBuddyChildDataSensor(coordinator, child, description)
                    new_entities.append(tracked[key])
            # One sensor per active timer
            for timer in coordinator.data[1].get(child_id, {}).get(ATTR_TIMERS, []):
                timer_id = timer[ATTR_ID]
                key = f"{child_id}_timer_{timer_id}"
                if key not in tracked:
                    tracked[key] = BabyBuddyTimerSensor(coordinator, child, timer_id)
                    new_entities.append(tracked[key])
        if new_entities:
            async_add_entities(new_entities)
