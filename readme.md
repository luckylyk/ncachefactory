#  NCacheManager
for Audodesk Maya 2017 (or higher)
Author: Lionel Brouyère

## Warning
This is beta, may contains lots of bug or unprevented cases.
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

Basically, maya is not really really to manage a versioning ncache. But during asset researchs or productions, that really important for artist to be able the doesn't take care so much about his versioning. Here versions are easy to manage, no more manual work. The settings and maps are saved for every version and easy to gather. So try it, rage quit cause of bugs, wait a fix and love it :).


### Installation
place the "ncachemanager" folder the into the maya script folder.

| os       | path                                          |
| ------   | ------                                        |
| linux    | ~/< username >/maya                           |
| windows  | \Users\<username>\Documents\maya              |
| mac os x | ~<username>/Library/Preferences/Autodesk/maya |

Ensure that you pick the ncachemanager-master subfolder.


### How to run
```python
import ncachemanager
ncachemanager.launch()
```
