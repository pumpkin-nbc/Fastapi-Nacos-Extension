# Configuration center

`await nacos.get_config(app, "application.yaml", group="DEFAULT_GROUP")`
returns the exact SDK text. FastAPI-Nacos intentionally does not parse YAML or
JSON, mutate application state, or install dynamic listeners. A missing item
therefore remains distinguishable from parsed data.

