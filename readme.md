CoNLL2016 Shallow Discourse Parsing
======
Soochow University Shallow Discourse Parsing System


Components
======
1. Connective Identification ==> connective.py

2. Argument Labeling ==> argument.py

3. Explicit Sense Classification ==> explicit.py

4. NonExplicit Sense Classification ==> nonexp.py

Running
======
Training each model respectively

``` python connective.py ```

``` python argument.py ```

``` python explicit.py ```

``` python nonexp.py ```

Get end-to-end result

``` python end2end.py -o ../report -r dev.out.json ```

=====
N.B. zh/ part is the final submission system for chinese shallow discourse parsing.
