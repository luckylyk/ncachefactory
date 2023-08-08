from ncachefactory.versioning import list_available_cacheversions


DEFAULT_VALUES = {
  "comment": "",
  "name": "batch ",
  "creation_time": 0,
  "modification_time": 0,
  "playblasts": [],
  "end_frame": 120,
  "nodes": {},
  "start_frame": 1
}

workspace_to_clean = ""
cacheversions = list_available_cacheversions(workspace_to_clean)
for cacheversion in cacheversions:
    for k, v in DEFAULT_VALUES.items():
        if cacheversion.infos.get(k) is None:
            print(cacheversion.name, "is out of date and doesn't have", k, "registered, default value set")
            cacheversion.infos[k] = v
            cacheversion.save_infos()
