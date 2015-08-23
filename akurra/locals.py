"""Locals module."""
from injector import Key

# Args
ArgLogLevel = Key('ArgLogLevel')

# General
ShutdownFlag = Key('ShutdownFlag')

# Debug
DebugFlag = Key('DebugFlag')
DebugToggleKey = Key('DebugToggleKey')

# Configuration
Configuration = Key('Configuration')

# Modules
ModuleEntryPointGroup = Key('ModuleEntryPointGroup')

# Display
DisplayClock = Key('DisplayClock')
DisplayMaxFPS = Key('DisplayMaxFPS')

# Events
EventPollTimeout = Key('EventPollTimeout')

# Assets
AssetBasePath = Key('AssetBasePath')

# Entities
EntityComponentEntryPointGroup = Key('EntityComponentEntryPointGroup')
EntitySystemEntryPointGroup = Key('EntitySystemEntryPointGroup')
EntityTemplates = Key('EntityTemplates')

# Session
SessionFilePath = Key('SessionFilePath')

# Audio
AudioMasterVolume = Key('AudioMasterVolume')
AudioBackgroundMusicVolume = Key('AudioBackgroundMusicVolume')
AudioSpecialEffectsVolume = Key('AudioSpecialEffectsVolume')
