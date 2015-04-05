"""Locals module."""
from injector import Key

# General
DebugFlag = Key('DebugFlag')
ShutdownFlag = Key('ShutdownFlag')

# Configuration
Configuration = Key('Configuration')

# Modules
ModuleEntryPointGroup = Key('ModuleEntryPointGroup')

# Display
DisplayScreen = Key('DisplayScreen')
DisplayClock = Key('DisplayClock')
DisplayResolution = Key('DisplayResolution')
DisplayFlags = Key('DisplayFlags')
DisplayMaxFPS = Key('DisplayMaxFPS')
DisplayCaption = Key('DisplayCaption')

# Events
EventPollTimeout = Key('EventPollTimeout')

# Assets
AssetBasePath = Key('AssetBasePath')

# Entities
EntityComponentEntryPointGroup = Key('EntityComponentEntryPointGroup')
EntitySystemEntryPointGroup = Key('EntitySystemEntryPointGroup')
EntityTemplates = Key('EntityTemplates')
