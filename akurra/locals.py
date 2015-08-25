"""Locals module."""
from injector import Key

# Args
ArgLogLevel = Key('ArgLogLevel')

# General shared flags and objects
ShutdownFlag = Key('ShutdownFlag')
DebugFlag = Key('DebugFlag')
DisplayClock = Key('DisplayClock')

# Configuration
Configuration = Key('Configuration')

# Assets
AssetBasePath = Key('AssetBasePath')

# Entities
EntityComponentEntryPointGroup = Key('EntityComponentEntryPointGroup')
EntitySystemEntryPointGroup = Key('EntitySystemEntryPointGroup')
EntityTemplates = Key('EntityTemplates')

# Session
SessionFilePath = Key('SessionFilePath')
