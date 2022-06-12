### Install

#### Poetry = Package manager
This project uses Poetry as a package manager.
Please refer to the [Poetry Installation docs](https://python-poetry.org/docs/#installation) or just run the following to install:
```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

#### Experiments - memory usage
Branch `ab/experiment-memory-usage`
 * EMPTY data structure, english, 540k words: 3.3MiB
 * FILLED data structure, english, 540k words: 273.63MiB ~= 530B per word