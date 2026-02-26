# slurdletwo

### _it's back now with 200% more slurs_

flask app that creates an endless quiz on racial slurs. you can probably use this to do data science

## how to run it

`uv sync` should set it up there is a `requirements.txt` too whatever floats your boat.

`--init` will pull the list of racial slurs from [the racial slur database](http://rsdb.org/) and pop
them in an sqlite3 db make
some csv files. `--refresh` does this but deletes the generated files first

`--weights` generates a csv with weights for each slur target using huggingface models. currently just using regex to
make sure the user isn't presented with targets that are too similar i.e. _asian_ and _asian/american_. not sure the
best way to teach a computer that _albanian_ and _balkan_ are semantically similar words

`--slurs` mostly for debugging it just prints the generated slur + targets etc
