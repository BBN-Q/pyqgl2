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

There are a number of things that keep theses functions from working:
* We have no good way to pass in arguments, so these (including
Qubits) must be hard coded in the `do*` methods in `*Min.py`. See
issue #62, etc.
* We don't yet have a good way to use the result of a `MEAS`, as in
`Reset` in `Feedback.py`. See issue #66.
* Qubits are not full objects so you can't use the `pulse_params`, as
in `doCPMG` or `doFlipFlop`. See issue #65.
* Various file reading methods fail, so Clifford sequence functions as
in `RB.py` fail. See issue #67, 68, 69.

