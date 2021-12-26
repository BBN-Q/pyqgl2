QGL2 versions of QGL.BasicSequences
- Used to test what can be done in QGL2, and show usage / programming patterns.

Each *.py has the QGL BasicSequence function(s), and a main() to show usage patterns. Typically, write a
python program that uses QGL2 main.py to compile a QGL2 program and then invokes that compiled program.

There are a number of things that keep these functions from working as desired:
* Issue #44: We have to supply all the qgl2main arguments currently
* We don't yet have a good way to use the result of a `MEAS`, as in `Reset` in `Feedback.py`. See issue #24.
* Qubits are not full objects so you can't use the `pulse_params`, as in `doCPMG` or `doFlipFlop`. See issue #37.
* Cliffords should be redone as QGL2 where possible, to avoid importing all of QGL1. But see issues #51-53

Todo includes:
* RB.py: Redo more of Cliffords as QGL2
* Feedback.py: Support using measurements
