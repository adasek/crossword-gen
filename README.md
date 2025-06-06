### Install

#### Requirements
For PyICU package it's nescessary to have the ICU library installed.
```bash
# Debian/Ubuntu
sudo apt install libicu-dev
```

#### Poetry = Package manager
This project uses Poetry as a package manager.
Please refer to the [Poetry Installation docs](https://python-poetry.org/docs/#installation) or just run the following to install:
```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

### Usage
#### Input word list
Create a pandas dataframe with columns:
 * word_label_text
 * word_description_text
 * word_concept_id
 * word_label_id
 * word_description_id
 * score

#### Creating a word list
Example when your words are in a text file, every word on its single line:
```python
import pandas as pd

word_list = list()
with open('words') as wordlist_file:
    for i, word in enumerate(wordlist_file.readlines()):
        word_list.append([word.strip().lower(), '', i, i, i])

words_dataframe = pd.DataFrame(data=word_list,
                               columns=['word_label_text',
                                        'word_description_text',
                                        'word_concept_id',
                                        'word_label_id',
                                        'word_description_id'])

words_dataframe.to_pickle('wordlist.pickle.gzip', compression='gzip', protocol=5)
```

#### Run the generator
```bash
poetry run python3 ./run.py
```


#### Experiments - memory usage
Branch `ab/experiment-memory-usage`
 * EMPTY data structure, english, 540k words: 3.3MiB
 * FILLED data structure, english, 540k words: 273.63MiB ~= 530B per word

### Updating
1) Enlist all upgradable dependencies:
```bash
poetry show --outdated --latest
```
2) Increase versions in `pyproject.toml`
```bash
poetry lock && poetry install
```


### Testing
Not much unit test is written yet.
```bash
poetry run python3 -m pytest
```
