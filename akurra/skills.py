"""Skills module."""
import logging

from .locals import *  # noqa
from .entities import EntityEvent, EntityInput, EntityInputChangeEvent, EntityManager, Component, System
from .modules import Module
from .utils import unit_vector_between


logger = logging.getLogger(__name__)


class EntitySkillUsageEvent(EntityEvent):

    """Entity skill usage event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


class SkillComponent(Component):

    """Base skill component."""


class TargetedSkillComponent(SkillComponent):

    """Base targeted skill component."""


class RangedTargetedSkillComponent(TargetedSkillComponent):

    """Base ranged target skill component."""

    def __init__(self, max_distance=None):
        """Constructor."""
        super().__init__()

        self.max_distance = max_distance


class EntityRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged entity target skill component."""


class PointRangedTargetedSkillComponent(RangedTargetedSkillComponent):

    """Base ranged point target skill component."""


class ManaConsumingSkillComponent(SkillComponent):

    """Base mana consuming skill component."""

    def __init__(self, mana={}):
        """Constructor."""
        super().__init__()

        self.mana = mana


class SkillsModule(Module):

    """Skills module."""

    def __init__(self):
        """Constructor."""
        self.configuration = self.container.get(Configuration)
        self.entities = self.container.get(EntityManager)

        # Merge skill templates into the other entity templates from the entity manager
        self.skill_templates = self.configuration.get('akurra.skills.templates', {})
        self.entities.entity_templates.update(self.skill_templates)

    # def start(self):
    #     """Start the module."""

    # def stop(self):
    #     """Stop the module."""


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
        EntityInputChangeEvent: ['on_entity_event', 10]
    }

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # Only proceed if we're here to use a skill
        if (event.input != EntityInput.SKILL_USAGE) or (event.input_state is False):
            return

        fireball = self.entities.create_entity_from_template('fireball')

        layer = entity.components['layer'].layer

        source = entity.components['physics'].collision_core.center
        target = entity.components['input'].input[EntityInput.TARGET_POINT]
        direction = unit_vector_between(source, target)

        fireball.components['position'].primary_position = source
        fireball.components['velocity'].direction = direction
        fireball.components['velocity'].speed = 150

        layer.add_entity(fireball)

        # Trigger a skill usage event
        # @TODO Add skill ID and state here
        self.events.dispatch(EntitySkillUsageEvent(entity.id))
