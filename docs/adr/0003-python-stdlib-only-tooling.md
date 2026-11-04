# Installer and mra-repo are Python, standard library only

`install.sh` is a thin entry point that checks for `python3` >= 3.11 and hands over to `install.py`; `mra-repo` is Python too. Merging `settings.json`, reading `mra-flow.toml`, and computing the checksum manifest are awkward and fragile in bash, and the SessionStart hook already requires Python, so Python adds no new prerequisite. Only the standard library is used (`tomllib`, `json`, `hashlib`, `unittest`), so nothing has to be installed with pip.
