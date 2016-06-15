CoNLL2016 Shallow Discourse Parsing
======
Soochow University Shallow Discourse Parsing System


Components
======
Connective Identification ==> connective.py
Argument Labeling ==> argument.py
Explicit Sense Classification ==> explicit.py
NonExplicit Sense Classification ==> nonexp.py

Running
======
1. training each model respectively
``` python connective.py ```
``` python argument.py ```
``` python explicit.py ```
``` python nonexp.py ```

2. get end-to-end result
``` python end2end.py -o ../report -r dev.out.json ```
