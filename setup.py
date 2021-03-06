#!/usr/bin/env python3
"""Setup module."""
from setuptools import setup, find_packages
import os


def read(fname):
    """Read and return the contents of a file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='akurra',
    version='0.0.1',
    description='Akurra - A pluggable game boilerplate',
    long_description=read('README'),

    author='Multatronic',
    author_email='contact@multatronic.com',

    url='https://github.com/multatronic/akurra',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
    ],

    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'akurra = akurra:main',
        ],

        'akurra.modules': [
            'display = akurra.display:DisplayModule',
            'debug = akurra.debug:DebugModule',
            'audio = akurra.audio:AudioModule',
            'mouse = akurra.mouse:MouseModule',
            'UI = akurra.ui:UIModule',

            'skills = akurra.skills:SkillsModule',

            'input = akurra.input:InputModule',
            'keyboard_input = akurra.keyboard:KeyboardInput',
            'mouse_input = akurra.mouse:MouseInput',
        ],

        'akurra.entities.components': [
            'health = akurra.entities:HealthComponent',
            'mana = akurra.entities:ManaComponent',
            'input = akurra.entities:InputComponent',
            'velocity = akurra.entities:VelocityComponent',
            'character = akurra.entities:CharacterComponent',
            'player = akurra.entities:PlayerComponent',
            'layer = akurra.entities:LayerComponent',
            'map_layer = akurra.entities:MapLayerComponent',
            'sprite = akurra.entities:SpriteComponent',
            'physics = akurra.entities:PhysicsComponent',
            'position = akurra.entities:PositionComponent',
            'state = akurra.entities:StateComponent',

            'point_ranged_targeted_skill = akurra.skills:PointRangedTargetedSkillComponent',
            'entity_ranged_targeted_skill = akurra.skills:EntityRangedTargetedSkillComponent',
            'mana_consuming_skill = akurra.skills:ManaConsumingSkillComponent',
            'damaging_skill = akurra.skills:DamagingSkillComponent',
            'health_modifying_skill = akurra.skills:HealthModifyingSkillComponent',
        ],

        'akurra.entities.systems': [
            'player_keyboard_input = akurra.entities:PlayerKeyboardInputSystem',
            'player_mouse_input = akurra.entities:PlayerMouseInputSystem',

            'velocity = akurra.entities:VelocitySystem',
            'movement = akurra.entities:MovementSystem',
            'collision = akurra.entities:CollisionSystem',
            'rendering = akurra.entities:RenderingSystem',
            'mana_gathering = akurra.entities:ManaGatheringSystem',
            'mana_replenishment = akurra.entities:ManaReplenishmentSystem',
            'player_terrain_sound = akurra.entities:PlayerTerrainSoundSystem',
            'sprite_rect_position_correction = akurra.entities:SpriteRectPositionCorrectionSystem',
            'sprite_render_ordering = akurra.entities:SpriteRenderOrderingSystem',
            'positioning = akurra.entities:PositioningSystem',
            'health_regeneration = akurra.entities:HealthRegenerationSystem',
            'death = akurra.entities:DeathSystem',

            'skill_usage = akurra.skills:SkillUsageSystem',
            'mana_consuming_skill = akurra.skills:ManaConsumingSkillSystem',
            'point_ranged_targeted_skill = akurra.skills:PointRangedTargetedSkillSystem',
            'entity_ranged_targeted_skill = akurra.skills:EntityRangedTargetedSkillSystem',
            'damaging_skill = akurra.skills:DamagingSkillSystem',
            'health_modifying_skill = akurra.skills:HealthModifyingSkillSystem',
        ],

        'akurra.games': [
            'demo = akurra.demo:DemoGame',
        ]
    },

    install_requires=[
        'pygame',
        'colorlog',
        'injector',
        'pytmx',
        'pyscroll',
        'pyganim',
        'BallerCFG'
    ],
    dependency_links=[
        'git+https://github.com/kalmanolah/ballercfg.git#egg=BallerCFG'
    ]
)
