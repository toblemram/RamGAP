# plaxis/utak/level1.py
import plxscripting
import encryption
import pandas as pd
from plxscripting.easy import new_server


def level1(port, passord):
    # Kobler til Plaxis-modell
    plx_server = 'localhost'
    s_i, g_i = new_server(plx_server, port, password=passord)

    # Henter ut informasjon om structures
    g_i.gotostructures()

    # Initierer lister
    Plates_name = []
    Plates_Xvalue = []
    Plate_ID = []
    EmbeddedBeamRow_name = []
    EmbeddedBeamRow_Xvalue = []
    EmbeddedBeamRow_ID = []

    # Henter ut navn på plater og embedded beam rows
    if hasattr(g_i, 'Plates'):
        for plate in g_i.Plates:
            Plates_name.append(plate.Name.value)
            Plates_Xvalue.append(str(plate.Parent.First.x.value))
            Plate_ID.append(plate)

    if hasattr(g_i, 'EmbeddedBeamRows'):
        for ebr in g_i.EmbeddedBeamRows:
            EmbeddedBeamRow_name.append(ebr.Name.value)
            EmbeddedBeamRow_Xvalue.append(str(ebr.Parent.First.x.value))
            EmbeddedBeamRow_ID.append(ebr)

    # Sammenslåing av navn og posisjon
    StructKallenavn = []
    for i, name in enumerate(Plates_name):
        StructKallenavn.append(f"Navn: {name}, x = {Plates_Xvalue[i]}")
    for i, name in enumerate(EmbeddedBeamRow_name):
        StructKallenavn.append(f"Navn: {name}, x = {EmbeddedBeamRow_Xvalue[i]}")

    # Henter ut informasjon om faser
    g_i.gotostages()
    nPhases = len(g_i.Phases)
    namesPhases = g_i.Phases.Identification.value
    idPhases = g_i.Phases[:]

    return StructKallenavn, namesPhases, idPhases