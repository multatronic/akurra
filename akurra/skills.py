"""Skills module."""
import math
import logging

from .locals import *  # noqa
from .entities import EntityEvent, EntityInput, EntityInputChangeEvent, EntityCollisionEvent, EntityManager, \
    Component, System
from .modules import Module
from .utils import unit_vector_between, map_unit_vector_to_angle


logger = logging.getLogger(__name__)


class EntitySkillUsageEvent(EntityEvent):

    """Entity skill usage event."""

    def __init__(self, entity_id, skill_entity_id):
        """Constructor."""
        super().__init__(entity_id)

        self.skill_entity_id = skill_entity_id


class SkillComponent(Component):

    """Base skill component."""


class TargetedSkillComponent(SkillComponent):

    """Base targeted skill component."""


class RangedTargetedSkillComponent(TargetedSkillComponent):

    """Base ranged target skill component."""

    def __init__(self, maximum_distance=None, travelling=True, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)

        self.maximum_distance = maximum_distance
        self.travelling = travelling


class EntityRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged entity target skill component."""


class PointRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged point target skill component."""


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
        'physics'  # @TODO This needs to go
    ]

    event_handlers = {
        EntityInputChangeEvent: ['on_entity_input_change_event', 10],
        EntityCollisionEvent: ['on_entity_collision_event', 10]
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
            # Not a a change of the skill usage input, or not the correct state
            return

        entity_input = entity.components['input'].input
        selected_skill = entity_input[EntityInput.SELECTED_SKILL]

        # Only proceed if we actually have a skill to use
        if not selected_skill:
            # No selected skill
            return

        skill = self.entities.create_entity_from_template(selected_skill)

        # If our skill requires a point target
        if 'point_ranged_targeted_skill' in skill.components:
            target_requirement = skill.components['point_ranged_targeted_skill']
            target_point = entity_input[EntityInput.TARGET_POINT]

            # Only proceed if we have a target point
            if not target_point:
                # No target point
                return

            source = None

            # If this is a travelling skill
            if target_requirement.travelling:
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

            # If we have a maximum distance set for our ranged target
            if target_requirement.maximum_distance:
                # Only proceed if our target point is not too far away from our source
                if distance_between(source, target_point) > target_requirement.maximum_distance:
                    # Target is located too far away
                    return

        # If our skill requires mana
        if 'mana_consuming_skill' in skill.components:
            entity_mana = entity.components['mana'].mana
            skill_mana = skill.components['mana_consuming_skill'].mana

            # For all types of required mana, ensure we have the required amount
            for mana_type in skill_mana:
                if skill_mana[mana_type] > entity_mana.get(mana_type, 0):
                    # Not enough mana
                    return

            # If we have enough mana, subtract the amount from the entity for all types
            for mana_type in skill_mana:
                entity_mana[mana_type] -= skill_mana[mana_type]

        # A skill with a position should be added to the layer the entity is on.. probably
        if 'position' in skill.components:
            entity.components['layer'].layer.add_entity(skill)

        # Trigger a skill usage event
        self.events.dispatch(EntitySkillUsageEvent(entity.id, skill.id))

        # Watch this skill
        self.used_skill_ids.append(skill.id)

    def on_entity_collision_event(self, event):
        """Handle a collision event."""
        # Only proceed if this is a collision for a skill that we are watching
        if event.entity_id not in self.used_skill_ids:
            # We aren't watching this skill
            return

        skill = self.entities.find_entity_by_id(event.entity_id)

        # Only proceed if this skill collided with an entity
        if event.collided_entity_id:
            target = self.entities.find_entity_by_id(event.collided_entity_id)

            # If this is a damaging skill
            if 'damaging_skill' in skill.components:
                skill_damage = skill.components['damaging_skill'].damage

                # Only proceed if the target entity has a health component
                if 'health' in target.components:
                    target_health = target.components['health']

                    # Loop through all damage types for this skill and damage target health
                    for damage_type in skill_damage:
                        # @TODO Take damage type into account (mitigations, resistances and stuff?)
                        target_health.health -= skill_damage[damage_type]

        # Remove this skill from its layer
        # @TODO Add an onremove callback in the components so they can unset certain things when removed?
        skill.components['layer'].layer.remove_entity(skill)

        # Remove this skill from the manager
        self.entities.remove_entity(skill)

        # Remove this skill from the watched list
        self.used_skill_ids.remove(skill.id)
