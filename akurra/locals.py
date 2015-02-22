"""Locals module."""
from injector import Key

# General
ShutdownFlag = Key('ShutdownFlag')

# Modules
ModuleEntryPointGroup = Key('ModuleEntryPointGroup')

# Display
Display = Key('Display')
DisplayClock = Key('DisplayClock')
DisplayResolution = Key('DisplayResolution')
DisplayFlags = Key('DisplayFlags')
DisplayMaxFPS = Key('DisplayMaxFPS')

# Events
EventPollTimeout = Key('EventPollTimeout')
