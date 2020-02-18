#  NCacheFactory
for Audodesk Maya 2017 (or higher)
Author: Lionel Brouyère

## Warning
This beta may contain a lot of bugs or unprevented cases.
Feel free to contribute or report bugs.

### Description
Versioning system for Maya nucleus technologies
Feature:
  - Automatic versioning system and file management
  - Make navigation and caching easy
  - Maya scene constantly cleaned
  - Settings and maps saved for each version and each node
  - Realtime value table analysis and comparison between scene values and connected cache
  - Save comment for every version
  - Support different namespaces
  - Playblast during simulation
  - Cache on batch with realtime feedback rendering
  - Attribute wedging with realtime comparison

Basically, Maya is not really made to manage a versioning ncache. But during asset research or production, this is really important for artist to be able to do. Here versions are easy to manage, no more manual work. The settings and maps are saved for every version and easy to gather. So try it, rage quit because of bugs, wait for a fix, and love it :).


### Installation
Download the repository folder and copy it anywhere on your computer.
Add the path to the PYTHONPATH environment variable path to get the module accessible by default in Maya and run the following command.

### How to run
```python
import ncachefactory
ncachefactory.launch()
```
n.b. if you don't have access to edit your Maya environment (e.g. special studio launcher). You can interactively add the path in a maya python console and launch the module like this:
```python
import sys
sys.path.append(r"{replace by the ncachemanager location folder}")
import ncachefactory
ncachefactory.launch()
```
