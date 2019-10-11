# QGL2 compiler steps

1. *NameSpaces* - Build name spaces from file-level imports. Identify the “qgl2main” function.
2. Make sure some basic things (Wait, Sync, and Barrier) can be found in the name space.
3. *Inliner* - Iteratively (up to 20 times) try to inline things until the program stops changing. (Note that we don’t have a mechanism to ask for a piece of code NOT to be inlined.)
4. *EvalTransformer* - Evaluate each expression.
5. Replace bindings with their values from evaluation.
6. *Flattener* - Flatten out repeat, range, ifs... Qiter, Qfor, etc
7. *SequenceExtractor* - Produce QGL1 sequence function

