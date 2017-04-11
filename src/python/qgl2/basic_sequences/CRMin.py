# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, QRegister
from qgl2.util import init
from qgl2.qgl1 import Id, flat_top_gaussian_edge, X, X90, echoCR
from qgl2.qgl1 import MEAS
from qgl2.basic_sequences.helpers import create_cal_seqs

import numpy as np
from math import pi

@qgl2decl
def doPiRabi():
    # FIXME: No arguments allowed
    qr = QRegister('q1', 'q2') # qr[0] is control, qr[1] is target
    # FIXME: Better values!?
    lengths = np.linspace(0, 4e-6, 11)
    riseFall=40e-9
    amp=1
    phase=0
    calRepeats=2

    # Sequence 1: Id(control), gaussian(l), measure both
    for l in lengths:
        init(qr)
        Id(qr[0])
        flat_top_gaussian_edge(qr[0], qr[1], riseFall, amp=amp, phase=phase, length=l)
        Barrier((qr,))
        MEAS(qr)

    # Sequence 2: X(control), gaussian(l), X(control), measure both
    for l in lengths:
        init(qr)
        X(qr[0])
        flat_top_gaussian_edge(qr[0], qr[1], riseFall, amp=amp, phase=phase, length=l)
        X(qr[0])
        Barrier((qr,))
        MEAS(qr)

    # Then do calRepeats calibration sequences
    create_cal_seqs(qr, calRepeats)

@qgl2decl
def doEchoCRLen():
    # FIXME: No arguments allowed
    qr = QRegister('q1', 'q2') # qr[0] is control, qr[1] is target
    # FIXME: Better values!?
    lengths = np.linspace(0, 2e-6, 11)
    riseFall=40e-9
    amp=1
    phase=0
    calRepeats=2

    # Sequence1:
    for l in lengths:
        init(qr)
        Id(qr[0])
        echoCR(qr[0], qr[1], length=l, phase=phase,
               riseFall=riseFall)
        Id(qr[0])
        Barrier((qr,))
        MEAS(qr)

    # Sequence 2
    for l in lengths:
        init(qr)
        X(qr[0])
        echoCR(qr[0], qr[1], length=l, phase=phase,
               riseFall=riseFall)
        X(qr[0])
        Barrier((qr,))
        MEAS(qr)

    # Then do calRepeats calibration sequences
    create_cal_seqs(qr, calRepeats)

@qgl2decl
def doEchoCRPhase():
    # FIXME: No arguments allowed
    qr = QRegister('q1', 'q2') # qr[0] is control, qr[1] is target
    # FIXME: Better values!?
    phases = np.linspace(0, pi/2, 11)
    riseFall=40e-9
    amp=1
    length=100e-9
    calRepeats=2

    # Sequence 1
    for ph in phases:
        init(qr)
        Id(qr[0])
        echoCR(qr[0], qr[1], length=length, phase=ph,
               riseFall=riseFall)
        X90(qr[1])
        Id(qr[0])
        Barrier((qr,))
        MEAS(qr)

    # Sequence 2
    for ph in phases:
        init(qr)
        X(qr[0])
        echoCR(qr[0], qr[1], length=length, phase=ph,
               riseFall=riseFall)
        X90(qr[1])
        X(qr[0])
        Barrier((qr,))
        MEAS(qr)

    # Then do calRepeats calibration sequences
    create_cal_seqs(qr, calRepeats)
