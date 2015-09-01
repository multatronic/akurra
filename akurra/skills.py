"""Skills module."""
import math
import logging

from .locals import *  # noqa
from .entities import EntityEvent, EntityInput, EntityInputChangeEvent, EntityCollisionEvent, EntityManager, \
    Component, System, EntityState, EntityStateChangeEvent
from .modules import Module
from .utils import unit_vector_between, map_unit_vector_to_angle


logger = logging.getLogger(__name__)


class EntitySkillUsageEvent(EntityEvent):

    """Entity skill usage event."""

    def __init__(self, entity_id, skill_entity_id):
        """Constructor."""
        super().__init__(entity_id)

        self.skill_entity_id = skill_entity_id


class EntitySkillUsageAttemptEvent(EntitySkillUsageEvent):

    """Entity skill usage attempt event."""


class SkillComponent(Component):

    """Base skill component."""


class HealthModifyingSkillComponent(Component):

    """Base health modifying skill component."""

    def __init__(self, health=0, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.health = health


class TargetedSkillComponent(SkillComponent):

    """Base targeted skill component."""


class RangedTargetedSkillComponent(TargetedSkillComponent):

    """Base ranged target skill component."""

    def __init__(self, maximum_distance=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.maximum_distance = maximum_distance


class EntityRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged entity target skill component."""


class PointRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged point target skill component."""

    def __init__(self, travelling=True, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.travelling = travelling


class ManaConsumingSkillComponent(SkillComponent):

    """Base mana consuming skill component."""

    def __init__(self, mana={}, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.mana = mana


class DamagingSkillComponent(SkillComponent):

    """Base damaging skill component."""

    def __init__(self, damage={}, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.damage = damage


class SkillsModule(Module):

    """Skills module."""

    def __init__(self):
        """Constructor."""
        self.configuration = self.container.get(Configuration)
        self.entities = self.container.get(EntityManager)

        # Grab skill templates
        self.skill_templates = self.configuration.get('akurra.skills.templates', {})

        # Merge skill templates into the other entity templates from the entity manager
        self.entities.entity_templates.update(self.skill_templates)


class SkillUsageSystem(System):

    """System for handling skill usage."""

    requirements = [
        'input',
        'position',
        'map_layer',
        'layer',
        'physics'
    ]

    event_handlers = {
        EntityInputChangeEvent: ['on_entity_input_change_event', 10],
        EntityCollisionEvent: ['on_entity_collision_event', 20]
    }

    def __init__(self):
        """Constructor."""
        super().__init__()

        self.used_skill_ids = []

    def on_entity_input_change_event(self, event):
        """Handle an input change event."""
        entity = self.entities.find_entity_by_id_and_components(event.entity_id, self.requirements)

        # Only proceed if we've found an entity
        if not entity:
            # No entity was found for the event's entity id and our required components
            return

        # Only proceed if we're here to use a skill
        if (event.input != EntityInput.SKILL_USAGE) or (event.input_state is False):
            # Not a change of the skill usage input, or not the correct state
            return

        entity_input = entity.components['input'].input
        selected_skill = entity_input[EntityInput.SELECTED_SKILL]

        # Only proceed if we actually have a skill to use
        if not selected_skill:
            # No selected skill
            return

        skill = self.entities.create_entity_from_template(selected_skill)

        # Have an EntitySkillUsageAttempt event handled directly without posting it on the event queue
        # Various skill systems will analyze whether the skill is eligible for using and return boolean
        # values indicating the result. By directly having the event handled we can also capture the
        # output of the handling and act on it. We only proceed if all systems handling the usage
        # attempt let it pass.
        if not self.events.handle(EntitySkillUsageAttemptEvent(entity.id, skill.id)):
            # One of the systems decided this skill cannot be used right now
            self.entities.remove_entity(skill)

            return

        # Fire an EntitySkillUsageEvent to have various systems prepare the skill for actual use.
        # Having this event handled directly without posting it on the queue prevents any of the
        # outcomes of the requirement validation done by the EntitySkillUsageAttemptEvent be changed
        self.events.handle(EntitySkillUsageEvent(entity.id, skill.id))

        # A skill with a position should be added to the layer the entity is on.. probably
        if 'position' in skill.components:
            entity.components['layer'].layer.add_entity(skill)

        # Watch this skill
        self.used_skill_ids.append(skill.id)

    def on_entity_collision_event(self, event):
        """Handle a collision event."""
        # Only proceed if this is a collision for a skill that we are watching
        if event.entity_id not in self.used_skill_ids:
            # We aren't watching this skill
            return

        skill = self.entities.find_entity_by_id(event.entity_id)

        # Remove this skill from the watched list
        self.used_skill_ids.remove(skill.id)

        # Remove this skill from its layer
        skill.components['layer'].layer.remove_entity(skill)

        # Remove this skill from the manager
        self.entities.remove_entity(skill)


class ManaConsumingSkillSystem(System):

    """Mana consuming skill system."""

    event_handlers = {
        EntitySkillUsageAttemptEvent: ['on_entity_skill_usage_attempt', 10],
        EntitySkillUsageEvent: ['on_entity_skill_usage', 10]
    }

    def on_entity_skill_usage_attempt(self, event):
        """Handle an entity skill usage attempt."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        entity_mana_component = entity.components.get('mana', None)
        skill_mana_component = skill.components.get('mana_consuming_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if not skill_mana_component:
            return

        # If our entity doesn't have the right component(s), we're not allowed to use the skill
        if not entity_mana_component:
            return False

        entity_mana = entity_mana_component.mana
        skill_mana = skill_mana_component.mana

        # For all types of required mana, ensure we have the required amount
        for mana_type in skill_mana:
            if skill_mana[mana_type] > entity_mana.get(mana_type, 0):
                # We are lacking the required amount of mana
                return False

    def on_entity_skill_usage(self, event):
        """Handle an entity skill usage."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        entity_mana_component = entity.components.get('mana', None)
        skill_mana_component = skill.components.get('mana_consuming_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        # If we are allowed to proceed past this point, we may assume the entity has the required
        # components as well
        if not skill_mana_component:
            return

        entity_mana = entity_mana_component.mana
        skill_mana = skill_mana_component.mana

        # If we have enough mana, subtract the amount from the entity for all types
        for mana_type in skill_mana:
            entity_mana[mana_type] -= skill_mana[mana_type]


class PointRangedTargetedSkillSystem(System):

    """Point ranged targeted skill system."""

    event_handlers = {
        EntitySkillUsageAttemptEvent: ['on_entity_skill_usage_attempt', 10],
        EntitySkillUsageEvent: ['on_entity_skill_usage', 10]
    }

    def on_entity_skill_usage_attempt(self, event):
        """Handle an entity skill usage attempt."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        skill_target_component = skill.components.get('point_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if not skill_target_component:
            return

        # NOTE: By proceeding beyond this point, we assume our entity attempting to use the skill
        # has already been checked for position, physics, map_layer, layer, input components
        # by the SkillUsageSystem.

        target_point = entity.components['input'].input[EntityInput.TARGET_POINT]

        # Only proceed if we have a target point
        if not target_point:
            # No target point
            return False

        # If we have a maximum distance set for our ranged target
        if skill_target_component.maximum_distance:
            # Only proceed if our target point is not too far away from our source
            if distance_between(source, target_point) > skill_target_component.maximum_distance:
                # Target is located too far away
                return False

    def on_entity_skill_usage(self, event):
        """Handle an entity skill usage."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        skill_target_component = skill.components.get('point_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        # If we are allowed to proceed past this point, we may assume the entity has the required
        # components as well
        if not skill_target_component:
            return

        # NOTE: By proceeding beyond this point, we assume our entity attempting to use the skill
        # has already been checked for position, physics, map_layer, layer, input components
        # by the SkillUsageSystem.

        source = None
        target_point = entity.components['input'].input[EntityInput.TARGET_POINT]

        # If this is a travelling skill
        if skill_target_component.travelling:
            entity_collision_core = entity.components['physics'].collision_core

            # Since it's a travelling skill, it should spawn at the location of the entity using it
            source = entity_collision_core.center

            # A travelling skill requires a direction to travel in, so calculate it
            skill_direction = unit_vector_between(source, target_point)
            skill.components['velocity'].direction = skill_direction

            # Ensure the skill is spawned outside of the entity collision rectangle
            # by offsetting the spawn point by a certain distance based on a combination of
            # the entity collision core's size (height or width, whichever is bigger)
            # and the skill collision core's size (height or width, whichever is bigger)
            skill_offset_distance = entity_collision_core.width / 2 \
                if entity_collision_core.width > entity_collision_core.height \
                else entity_collision_core.height / 2

            skill_collision_core = skill.components['physics'].collision_core

            skill_offset_distance += skill_collision_core.width \
                if skill_collision_core.width > skill_collision_core.height \
                else skill_collision_core.height

            # Calculate a new spawn point for the skill based on the old spawn point, the
            # calculated angle of the skill and the offset distance
            skill_angle = map_unit_vector_to_angle(skill_direction)
            source = [source[0] + skill_offset_distance * math.cos(skill_angle),
                      source[1] + skill_offset_distance * math.sin(skill_angle)]

            # Modify the spawn point of the skill to ensure that the collision core
            # is centered on the spawn point
            source[0] -= skill_collision_core.width / 2
            source[1] -= skill_collision_core.height / 2

        # If this is not a travelling skill
        else:
            # Since this skill doesn't travel, it should spawn at the target point directly
            source = list(target_point)

        # Set the primary position for our skill
        skill.components['position'].primary_position = source


class EntityRangedTargetedSkillSystem(System):

    """Entity ranged targeted skill system."""

    event_handlers = {
        EntitySkillUsageAttemptEvent: ['on_entity_skill_usage_attempt', 10]
    }

    def on_entity_skill_usage_attempt(self, event):
        """Handle an entity skill usage attempt."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        skill_target_component = skill.components.get('entity_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if not skill_target_component:
            return

        target_entity_id = entity.components['input'].input[EntityInput.TARGET_ENTITY]

        # If we have no target entity ID, we can't use this skill
        if not target_entity_id:
            # No target
            return False

        target = self.entities.find_entity_by_id(target_entity_id)

        # If the target entity no longer exists, we can't use this skill
        if not target:
            # No target
            return False

        # If we have a maximum distance set for our ranged target
        if skill_target_component.maximum_distance:
            target_position = target.components['position'].primary_position

            # Only proceed if our target entity is not too far away from our source
            if distance_between(source, target_position) > skill_target_component.maximum_distance:
                # Target is located too far away
                return False


class DamagingSkillSystem(System):

    """Damaging skill system."""

    event_handlers = {
        EntityCollisionEvent: ['on_entity_collision', 10],
        EntitySkillUsageEvent: ['on_entity_skill_usage', 10]
    }

    def on_entity_collision(self, event):
        """Handle an entity skill usage."""
        # Only proceed if this entity collided with another entity
        if not event.collided_entity_id:
            return

        skill = self.entities.find_entity_by_id(event.entity_id)
        target = self.entities.find_entity_by_id(event.collided_entity_id)

        skill_damage_component = skill.components.get('damaging_skill', None)
        skill_target_component = skill.components.get('point_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if (not skill_damage_component) or (not skill_target_component):
            return

        self.perform_damage(target, skill_damage_component.damage)

    def on_entity_skill_usage(self, event):
        """Handle an entity skill usage."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        skill_damage_component = skill.components.get('damaging_skill', None)
        skill_target_component = skill.components.get('entity_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if (not skill_damage_component) or (not skill_target_component):
            return

        # NOTE: By proceeding beyond this point, we assume our entity attempting to use the skill
        # has already been checked for position, physics, map_layer, layer, input components
        # by the SkillUsageSystem.

        target_entity_id = entity.components['input'].input[EntityInput.TARGET_ENTITY]

        # If we have no target entity ID, don't proceed
        if not target_entity_id:
            return

        target = self.entities.find_entity_by_id(target_entity_id)

        # If the target entity no longer exists, don't proceed
        if not target:
            return

        self.perform_damage(target, skill_damage_component.damage)

    def perform_damage(self, entity, damage):
        """Perform damage to an entity's health."""
        health_component = entity.components.get('health', None)

        # If our target doesn't have the right component(s), this system isn't supposed to handle it
        if not health_component:
            return

        # Loop through all damage types and damage health
        for damage_type in damage:
            # @TODO Take damage type into account (mitigations, resistances and stuff?)
            health_component.health -= damage[damage_type]

        # If the resulting health is too large, set it to the maximum
        if health_component.health > health_component.max:
            health_component.health = health_component.max

        # If the resulting health is too small, set it to the minimum and trigger a
        # state change
        elif health_component.health <= health_component.min:
            health_component.health = health_component.min

            entity.components['state'].state = EntityState.DEAD
            self.events.dispatch(EntityStateChangeEvent(entity.id, EntityState.DEAD))


class HealthModifyingSkillSystem(System):

    """Health modifying skill system."""

    event_handlers = {
        EntitySkillUsageEvent: ['on_entity_skill_usage', 10]
    }

    def on_entity_skill_usage(self, event):
        """Handle an entity skill usage."""
        entity = self.entities.find_entity_by_id(event.entity_id)
        skill = self.entities.find_entity_by_id(event.skill_entity_id)

        skill_health_modifying_component = skill.components.get('health_modifying_skill', None)
        skill_target_component = skill.components.get('entity_ranged_targeted_skill', None)

        # If our skill doesn't have the right component(s), this system isn't supposed to handle it
        if (not skill_health_modifying_component) or (not skill_target_component):
            return

        # NOTE: By proceeding beyond this point, we assume our entity attempting to use the skill
        # has already been checked for position, physics, map_layer, layer, input components
        # by the SkillUsageSystem.

        target = self.entities.find_entity_by_id(entity.components['input'].input[EntityInput.TARGET_ENTITY])

        # If the target entity no longer exists, don't proceed
        if not target:
            return

        target_health_component = target.components.get('health', None)

        # If our target doesn't have the right component(s), this system isn't supposed to handle it
        if not target_health_component:
            return

        # Modify target health
        target_health_component.health += skill_health_modifying_component.health

        # If the resulting health is too large, set it to the maximum
        if target_health_component.health > target_health_component.max:
            target_health_component.health = target_health_component.max

        # If the resulting health is too small, set it to the minimum + 1
        # (this isn't a system for causing death, you know)
        elif target_health_component.health <= target_health_component.min:
            target_health_component.health = target_health_component.min + 1
