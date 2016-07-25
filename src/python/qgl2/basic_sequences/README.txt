QGL2 versions of QGL.BasicSequences

The *Min files are closer to working QGL2 versions.
The base versions include rewritten QGL1 versions, and first cut QGL2
versions.
But in QGL2, the function that produces the sequence does not compile
it; hence the move to the *Min files (no more use of compileAndWait, etc).
The *Min files also remove arguments from the main function.
Look for FIXME comments about things that do not currently work.

The base files generally have a main, intended to help unit test these
files. That main has not been run in a while.

There are a number of things that keep theses functions from working
* assignign the results of np.* to a variable fails to import the
function
* import of pi fails
* zip/product imports fail
* looping over functions broke again
* Our qubit is a stub; so explicit references to qubit.pulseParams
fail
* shapeFun argument of a function reference fails

