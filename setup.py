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
            'debug = akurra.debug:DebugModule',
            'keyboard = akurra.keyboard:KeyboardManager',
            'mouse = akurra.mouse:MouseManager',
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
            'dialog = akurra.entities:DialogComponent',
            'sprite = akurra.entities:SpriteComponent',
            'physics = akurra.entities:PhysicsComponent',
            'position = akurra.entities:PositionComponent'
        ],

        'akurra.entities.systems': [
            'player_input = akurra.entities:PlayerInputSystem',
            'velocity = akurra.entities:VelocitySystem',
            'movement = akurra.entities:MovementSystem',
            'collision = akurra.entities:CollisionSystem',
            'rendering = akurra.entities:RenderingSystem',
            'dialog = akurra.entities:DialogSystem',
            'player_terrain_sound = akurra.entities:PlayerTerrainSoundSystem',
            'sprite_rect_position_correction = akurra.entities:SpriteRectPositionCorrectionSystem',
            'sprite_render_ordering = akurra.entities:SpriteRenderOrderingSystem',
            'positioning = akurra.entities:PositioningSystem'
        ]
    },

    install_requires=[
        'pygame',
        'colorlog',
        'injector',
        'pytmx',
        'pyscroll',
        'BallerCFG'
    ],
    dependency_links=[
        'git+https://github.com/kalmanolah/ballercfg.git#egg=BallerCFG'
    ]
)
