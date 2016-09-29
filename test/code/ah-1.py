from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.qgl1 import Id, QubitFactory, MEAS
from qgl2.qgl2 import qgl2decl, qgl2stub, qbit, pulse, qgl2main

def read_ac_lines(fname):

    lines = open(fname, 'r').readlines()
    ac_lines = list()

    for line in lines:
        ac_lines.append([int(num.strip()) for num in line.split(',')])

    return ac_lines

@qgl2decl
def getACPulse(qubit: qbit, pulseNum) -> pulse:
    if pulseNum == 0:
        Id(qubit, len=2e-8)
    else:
        AC(qubit, pulseNum)

@qgl2stub('QGL.PulsePrimitives')
def AC(qubit: qbit, cliffNum) -> pulse:
    pass

@qgl2decl
def create_seqs(qubit: qbit, fileName):

    lines = read_ac_lines(fileName)

    for line in lines:
        for pulseNum in line:
            getACPulse(qubit, int(pulseNum))
        MEAS(qubit)

    # FIXME: create_cal_seqs doesn't work right yet
    # create_cal_seqs((qubit,), 500)

@qgl2main
def runPerfTest():
    qubit = QubitFactory('q1')
    fileName = "ah-1.csv"
    create_seqs(qubit, fileName)

