"""Skills module."""
import logging

from .entities import EntityEvent, EntityInput, EntityCollisionEvent, EntityInputChangeEvent, System
from .utils import unit_vector_between


logger = logging.getLogger(__name__)


class EntitySkillUsageEvent(EntityEvent):

    """Entity skill usage event."""

    def __init__(self, entity_id):
        """Constructor."""
        super().__init__(entity_id)


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
        EntityInputChangeEvent: ['on_entity_event', 10],
        EntityCollisionEvent: ['on_entity_collision_event', 10]
    }

    used_skill_ids = []

    def update(self, entity, event=None):
        """Have an entity updated by the system."""
        # Only proceed if we're here to use a skill
        if (event.input != EntityInput.SKILL_USAGE) or (event.input_state is False):
            return

        fireball = self.entities.create_entity_from_template('projectile')

        layer = entity.components['layer'].layer

        source = entity.components['physics'].collision_core.center
        target = entity.components['input'].input[EntityInput.TARGET_POINT]
        direction = unit_vector_between(source, target)

        # determine which side of the collision rect to spawn the fireball on
        center = direction[0] == 0 and direction[1] == 0
        # exempt center, since the player would shoot himself
        if not center:
            left = direction[0] < 0
            bottom = direction[1] > 0
            top = direction[1] < 0

            fireball_collision_pad = 5
            fireball_width = fireball.components['physics'].collision_core.width + fireball_collision_pad
            fireball_height = fireball.components['physics'].collision_core.height + fireball_collision_pad

            if left:
                if bottom:
                    # spawn fireball bottom left of player collision rect
                    logging.info('bottom left')
                    fireball_spawn_position = list(entity.components['physics'].collision_core.bottomleft)
                    fireball_spawn_position[1] += fireball_height
                elif top:
                    logging.info('top left')
                    # spawn fireball top left of player collision rect
                    fireball_spawn_position = list(entity.components['physics'].collision_core.topleft)
                    fireball_spawn_position[1] -= fireball_height
                else:
                    logging.info('left')
                    # spawn fireball left of player collision rect
                    fireball_spawn_position = list(entity.components['physics'].collision_core.left)
                fireball_spawn_position[0] -= fireball_width
            else:
                if bottom:
                    logging.info('bottom right')
                    # spawn fireball bottom right of player collision rect
                    fireball_spawn_position = list(entity.components['physics'].collision_core.bottomright)
                    fireball_spawn_position[1] += fireball_height
                elif top:
                    logging.info('top right')
                    # spawn fireball top right of player collision rect
                    fireball_spawn_position = list(entity.components['physics'].collision_core.topright)
                    fireball_spawn_position[1] -= fireball_height
                else:
                    logging.info('right')
                    # spawn fireball righ of player collision rect
                    fireball_spawn_position = list(entity.components['physics'].collision_core.right)
                fireball_spawn_position[0] += fireball_width


            fireball.components['position'].primary_position = fireball_spawn_position
            fireball.components['velocity'].direction = direction
            fireball.components['velocity'].speed = 150

            layer.add_entity(fireball)

            # Trigger a skill usage event
            # @TODO Add skill ID and state here
            self.events.dispatch(EntitySkillUsageEvent(entity.id))
            self.used_skill_ids.append(entity.id)

    def on_entity_collision_event(self, event):
        """Handle an event which contains a reference to an entity."""
        original_entity_id = event.entity_id
        collided_entity_id = event.collided_entity_id

        if original_entity_id in self.used_skill_ids:
            logging.debug('FIREBALL HIT %s', original_entity_id)
