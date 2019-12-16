#  NCacheFactory
for Audodesk Maya 2017 (or higher)
Author: Lionel Brouyère

## Warning
This beta may contains lots of bugs or unprevented cases.
Feel free to contribute or report bugs.

### Description
Versioning system for maya nucleus technologies
Feature:
  - Automatic versionning system and file management
  - Make navigation and caching easy
  - Maya scene constantly cleaned
  - Settings and map saved for each version and each node
  - Realtime values table analyse and comparison between scene values and connected cache
  - Save comment for every version
  - Support different namespace
  - Playblast during simulation
  - Cache on batch with realtime feedback rendering
  - Attribute wedging with realtime comparison

Basically, maya is not really really to manage a versioning ncache. But during asset researchs or productions, that really important for artist to be able the doesn't take care so much about his versioning. Here versions are easy to manage, no more manual work. The settings and maps are saved for every version and easy to gather. So try it, rage quit cause of bugs, wait a fix and love it :).


### Installation
Download the repository folder and copy it anywhere on youre computer.
Add the path to the PYTHONPATH environment variable path to get the module accessible by default in maya and run the following command.

### How to run
```python
import ncachefactory
ncachefactory.launch()
```
n.b. if you doesn't have access to edit your maya environment (e.g. special studio launcher). You can interactively add the path in a maya python console and launch the module like this:
```python
import sys
sys.path.append("r{replace by the ncachemanager location folder}")
import ncachefactory
ncachefactory.launch()
```
