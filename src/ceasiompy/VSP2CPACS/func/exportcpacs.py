
"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

The geometry is built in OpenVSP, saved as a .vsp3 file, and then selected in the GUI.
It is subsequently processed by this module to generate a CPACS file.

| Author: Nicolo Perasso
| Creation: 23/12/2025
"""

# Imports
import re
import defusedxml
import numpy as np
import xml.etree.ElementTree as ET  # nosec B405

from pathlib import Path
from defusedxml import ElementTree as DefusedElementTree

from ceasiompy import log


defuse = getattr(defusedxml, "defuse_stdlib", None)
if defuse is None:  # pragma: no cover
    raise ImportError("defusedxml does not support defuse_stdlib in this version.")
defuse()


# Functions
def safe_parse_xml(*args, **kwargs):
    return DefusedElementTree.parse(*args, **kwargs)


def safe_fromstring_xml(text: str):
    return DefusedElementTree.fromstring(text)


def make(doc, name, parent=None, text=None, **attrs):
    """
    Create an XML element, optionally add attributes, text value,
    and append to a parent element.
    """
    node = doc.createElement(name)

    # set attributes
    for k, v in attrs.items():
        node.setAttribute(k, str(v))

    # optional text
    if text is not None:
        node.appendChild(doc.createTextNode(str(text)))

    # optional parent
    if parent is not None:
        parent.appendChild(node)

    return node


def add_text(doc, name, parent, value):
    make(doc, name, parent, text=value)


def segment(doc, Parent, Name_wing, Name_Element, Name_Element_before, idx):
    segment = doc.createElement('segment')
    segment.setAttribute('uID', f'{Name_wing}Seg{idx}')
    Parent.appendChild(segment)
    name = doc.createElement('name')
    name.appendChild(doc.createTextNode(f'{Name_wing}Seg{idx}'))
    segment.appendChild(name)
    FromElement = doc.createElement('fromElementUID')
    FromElement.appendChild(doc.createTextNode(Name_Element_before))
    segment.appendChild(FromElement)
    toElement = doc.createElement('toElementUID')
    toElement.appendChild(doc.createTextNode(Name_Element))
    segment.appendChild(toElement)


def initialization(doc,data,name_file):
    cpacs = doc.createElement('cpacs')
    cpacs.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    cpacs.setAttribute("xsi_noNamespaceSchemaLocation", "CPACS_21_Schema.xsd")
    doc.appendChild(cpacs)

    # --- HEADER ---
    header = make(doc, 'header', cpacs)
    make(doc, 'name', header, name_file)
    make(doc, 'version', header, '0.2')
    make(doc, 'cpacsVersion', header, '3.0')

    versionInfos = make(doc, 'versionInfos', header)
    versionInfo = make(doc, 'versionInfo', versionInfos, version="version1")
    make(doc, 'description', versionInfo, 'Geometry from openVSP')
    make(doc, 'creator', versionInfo, 'cpacs2to3')
    make(doc, 'version', versionInfo, '0.3')
    make(doc, 'cpacsVersion', versionInfo, '3.0')
    make(doc, 'timestamp', versionInfo, '2025-10-30T13:40:44')

    # --- VEHICLES ---
    vehicles = make(doc, 'vehicles', cpacs)

    keys = list(data.keys())
    for i, k in enumerate(keys):

        if data[k]["Transformation"]["idx_engine"] is not None:

            transformation = data[k]["Transformation"]
            NameEngine = f"{transformation['Name']}_Engine{transformation['idx_engine']}"
            engines = make(doc, 'engines', vehicles)

            # ENGINE
            engine = make(doc, 'engine', engines, uID=NameEngine)
            make(doc, 'name', engine, NameEngine)

            # NACELLE
            nacelle = make(doc, 'nacelle', engine, uID=f'{NameEngine}_Nacelle')

            # CASE 1 : Normal nacelle
            prev_trans = data[keys[i - 1]]["Transformation"]
            if prev_trans["Name_type"] != "Duct":

                fanCowl = make(doc, 'fanCowl', nacelle, uID=f'{NameEngine}_Nacelle_fanCowl')

                sections = make(doc, 'sections', fanCowl)
                section = make(doc, 'section', sections, uID=f'{NameEngine}_Nacelle_fanCowl_Sec1')
                make(
                    doc,
                    'profileUID', section,
                    f"{NameEngine}_Nacelle_fanCowl_{data[k]['Airfoil']}"
                )

                Transformation(
                    doc,
                    section,
                    f"{NameEngine}_Nacelle_fanCowl_Sec1",
                    [
                        data[k]["Transformation"]["chord"],
                        1,
                        data[k]["Transformation"]["chord"] / 2,
                    ],
                    [0, 0, 0],
                    [0, 0, 0.5],
                )

                rotationCurve = make(
                    doc,
                    'rotationCurve',
                    fanCowl,
                    uID=f'{NameEngine}_Nacelle_fanCowl_RotCurve',
                )
                make(doc, 'referenceSectionUID', rotationCurve,
                     f'{NameEngine}_Nacelle_fanCowl_Sec1')
                make(doc, 'curveProfileUID', rotationCurve, f'{NameEngine}_fanCowlRotationCurve')
                make(doc, 'startZeta', rotationCurve, '-0.28')
                make(doc, 'endZeta', rotationCurve, '-0.25')
                make(doc, 'startZetaBlending', rotationCurve, '-0.3')
                make(doc, 'endZetaBlending', rotationCurve, '-0.23')

            # CASE 2 : Duct + Duct
            elif (
                prev_trans["Name_type"] == "Duct"
                and data[k]["Transformation"]["Name_type"] == "Duct"
            ):

                coreCowl = make(doc, 'coreCowl', nacelle, uID=f'{NameEngine}_coreCowl')

                sections = make(doc, 'sections', coreCowl)
                section = make(doc, 'section', sections, uID=f'{NameEngine}_coreCowl_Sec1')
                make(doc, 'profileUID',
                     section, f"{NameEngine}_Nacelle_coreCowl_{data[k]['Airfoil']}")

                Transformation(
                    doc,
                    section,
                    f"{NameEngine}_coreCowl_Sec1",
                    [
                        data[k]["Transformation"]["chord"],
                        1,
                        data[k]["Transformation"]["chord"] / 2,
                    ],
                    [0, 0, 0],
                    [
                        0,
                        0,
                        (0.5 * data[k]["Transformation"]["height"])
                        / data[keys[i - 1]]["Transformation"]["height"],
                    ],
                )

                rotationCurve = make(doc, 'rotationCurve',
                                     coreCowl, uID=f'{NameEngine}_coreCowl_RotCurve')
                make(doc, 'referenceSectionUID', rotationCurve, f'{NameEngine}_coreCowl_Sec1')
                make(doc, 'curveProfileUID', rotationCurve, f'{NameEngine}_coreCowlRotationCurve')
                make(doc, 'startZeta', rotationCurve, '-0.28')
                make(doc, 'endZeta', rotationCurve, '-0.25')
                make(doc, 'startZetaBlending', rotationCurve, '-0.3')
                make(doc, 'endZetaBlending', rotationCurve, '-0.23')

            # CASE 3 : Duct + Duct + Pod
            elif data[k]['Transformation']['Name_type'] == 'Pod':

                centerCowl = make(doc, 'centerCowl', nacelle, uID=f'{NameEngine}_centerCowl')
                make(doc, 'curveUID', centerCowl, f'{NameEngine}_centerCowlRotationCurve')

                offset_val = (
                    data[keys[i - 2]]["Transformation"]["X_Trasl"][0]
                    - data[keys[i - 2]]["Transformation"]["chord"] / 2
                    - data[k]["Transformation"]["X_Trasl"][0]
                    - data[keys[i - 2]]["Transformation"]["chord"] / 2
                )

                make(doc, 'xOffset', centerCowl, offset_val)

    # --- AIRCRAFT BODY ---
    aircraft = make(doc, 'aircraft', vehicles)
    model = make(doc, 'model', aircraft, uID='CPACS_test')
    make(doc, 'name', model, 'CPACS_test')

    # --- REFERENCE DATA ---
    reference = make(doc, 'reference', model)
    make(doc, 'area', reference, '1')
    make(doc, 'length', reference, '1')

    point = make(doc, 'point', reference, uID='Point')
    make(doc, 'x', point, '0')
    make(doc, 'y', point, '0')
    make(doc, 'z', point, '0')

    return doc, model, vehicles


def Transformation(doc, Parent, Name, X_scal, X_Rot, X_Trasl, abs_or_rel=None):
    transformation = make(doc, 'transformation', Parent, uID=f'{Name}_Tr')

    txt = ['x', 'y', 'z']
    x_Transf = np.column_stack((X_scal, X_Rot, X_Trasl))

    labels = ['scaling', 'rotation', 'translation']
    labels_uID = ['Scal', 'Rot', 'Transl']

    for idx, label in enumerate(labels):

        child = make(doc, label, transformation, uID=f'{Name}_Tr_{labels_uID[idx]}')

        # Only translation may contain refType attribute
        if idx == 2 and abs_or_rel is not None:
            child.setAttribute('refType', 'absGlobal' if abs_or_rel else 'absLocal')

        # x, y, z coordinates
        for i, ax in enumerate(txt):
            make(doc, ax, child, x_Transf[i, idx])


def Wing_section(doc, Parent, Name_wing, Section_key, Sections_parameters):

    # Extract numeric index at the end of the section key
    match = re.search(r'\d+$', Section_key)
    number = int(match.group()) if match else 0

    # --- Section UID ---
    uID_section_root = f'{Name_wing}Sec{number}'

    # Create section element
    section_root = make(doc, 'section', Parent, uID=uID_section_root)

    # Section name
    make(doc, 'name', section_root, uID_section_root)

    # --- Transformation parameters ---
    x_Scal = [
        Sections_parameters[Section_key]["x_scal"],
        Sections_parameters[Section_key]["y_scal"],
        Sections_parameters[Section_key]["z_scal"],
    ]
    x_Rot = np.zeros(3)
    x_Trasl = [
        Sections_parameters[Section_key]["x_trasl"],
        0,
        0,
    ]

    # --- Transformation ---
    Transformation(
        doc,
        section_root,
        uID_section_root,
        x_Scal,
        x_Rot,
        x_Trasl,
        Sections_parameters["Transformation"]["abs_system"],
    )

    # --- Element definition for the section ---
    Element(
        doc,
        section_root,
        uID_section_root,
        Section_key,
        Sections_parameters
    )


def Fuse_section(doc, Parent, Name, Section_key, Sections_parameters):

    # Extract numeric index at the end of the section key
    match = re.search(r'\d+$', Section_key)
    number = int(match.group()) if match else 0

    # --- Section UID ---
    uID_section = f'{Name}Sec{number}'

    # Create section element
    section = make(doc, 'section', Parent, uID=uID_section)

    # Section name
    make(doc, 'name', section, uID_section)

    # --- Transformation parameters ---
    X_Scal = [
        Sections_parameters[Section_key]["x_scal"],
        Sections_parameters[Section_key]["y_scal"],
        Sections_parameters[Section_key]["z_scal"],
    ]

    X_Rot = [
        Sections_parameters[Section_key]["x_rot"],
        Sections_parameters[Section_key]["y_rot"],
        Sections_parameters[Section_key]["z_rot"],
    ]

    X_Trasl = [
        0,
        Sections_parameters[Section_key]["y_trasl"],
        Sections_parameters[Section_key]["z_trasl"],
    ]

    # --- Transformation ---
    Transformation(
        doc,
        section,
        uID_section,
        X_Scal,
        X_Rot,
        X_Trasl,
        Sections_parameters["Transformation"]["abs_system"],
    )

    # --- Element definition of the fuselage section ---
    Fuse_Element(
        doc,
        section,
        uID_section,
        Section_key,
        Sections_parameters
    )


def Fuse_Element(doc, Parent, Name_section, Section_key, Section_parameters):

    # Element UID based on the section name
    Name_element = f'{Name_section}Elem'

    # Create <elements> container
    Elements = make(doc, 'elements', Parent)

    # Create <element> with uID
    Element = make(doc, 'element', Elements, uID=Name_element)

    # Element name tag
    make(doc, 'name', Element, Name_element)

    # Refers to fuselage airfoil profile
    profile_uid_str = f"{Name_section}_{Section_parameters[Section_key]['Airfoil']}"
    make(doc, 'profileUID', Element, profile_uid_str)

    # Identity transformation for the element (external function)
    x_Scal = np.ones(3)
    x_Rot = np.zeros(3)
    x_Trasl = np.zeros(3)

    Transformation(
        doc,
        Element,
        Name_element,
        x_Scal,
        x_Rot,
        x_Trasl,
        Section_parameters['Transformation']['abs_system']
    )


def Fuse_positioning(doc, Parent, Name, Section_key, Section_parameters, length_before_perc):

    # Extract section index and prefix (letters only)
    number = int(''.join(filter(str.isdigit, Name)))
    prefix = Name.rstrip('0123456789')

    # Create <positioning> element with uID
    positioning = make(doc, 'positioning', Parent, uID=f'{Name}GenPos')

    # Name tag
    make(doc, 'name', positioning, f'{Name}GenPos')

    # Fixed sweep and dihedral values for fuselage
    make(doc, 'sweepAngle', positioning, '90')
    make(doc, 'dihedralAngle', positioning, '0')

    # First fuselage section (no length)
    if number == 0:
        make(doc, 'length', positioning, '0')
        make(doc, 'toSectionUID', positioning, Name)
        length_before_perc.append(0)

    else:
        # Section longitudinal spacing
        section_length = float(
            Section_parameters[Section_key]['x_loc']
        ) - float(length_before_perc[-1])
        length_before_perc.append(float(Section_parameters[Section_key]['x_loc']))

        make(doc, 'length', positioning, str(section_length))

        # Connect from previous to current fuselage section
        Name_prev = f"{prefix}{number - 1}"
        make(doc, 'fromSectionUID', positioning, Name_prev)
        make(doc, 'toSectionUID', positioning, Name)


def Fuse_Profile(doc, Parent, Section_parameters, Section_key, uid):

    # Create fuselage profile element with uID
    fuselageProfile = make(doc, 'fuselageProfile', Parent, uID=str(uid))

    # Name and description
    make(doc, 'name', fuselageProfile, str(uid))
    make(doc, 'description', fuselageProfile, 'Profile from OpenVSP')

    # Coordinates container
    pointList = make(doc, 'pointList', fuselageProfile)

    txt = ['x', 'y', 'z']
    y_values = Section_parameters[Section_key]['Airfoil_coordinates'][0]
    z_values = Section_parameters[Section_key]['Airfoil_coordinates'][1]
    x_values = np.zeros(np.shape(y_values))

    # CPACS vector formatting
    x_cpacs = np.column_stack((x_values, y_values, z_values))

    for tag, elem in enumerate(txt):
        values_str = ' '.join(str(x_cpacs[:, tag]).strip().split()) \
                        .replace('[ ', '').replace(
                            '[', '').replace(' ]', '').replace(']', '').replace(' ', ';')
        child = make(doc, elem, pointList, values_str)
        child.setAttribute('mapType', 'vector')


def Element(doc, Parent, Name_section, Section_key, Section_parameters):

    Name_element = f'{Name_section}Elem'

    # Create elements container
    Elements = make(doc, 'elements', Parent)

    # Create element with uID
    Element = make(doc, 'element', Elements, uID=Name_element)

    # Name tag
    make(doc, 'name', Element, Name_element)

    # Airfoil UID reference
    airfoil_str = f"{Name_section}_{Section_parameters[Section_key]['Airfoil']}"
    make(doc, 'airfoilUID', Element, airfoil_str)

    # Identity transformation (external function)
    x_Scal = np.ones(3)
    x_Rot = np.zeros(3)
    x_Trasl = np.zeros(3)

    Transformation(
        doc,
        Element,
        Name_element,
        x_Scal,
        x_Rot,
        x_Trasl,
        Section_parameters['Transformation']['abs_system']
    )


def Wing_positioning(doc, Parent, Name, Section_key, Sections_parameters, dih_list):
    # Create positioning element with uID
    positioning = make(doc, 'positioning', Parent, uID=f'{Name}GenPos')
    make(doc, 'name', positioning, f'{Name}GenPos')

    # First wing section
    if Name[-1] == '0':
        make(doc, 'length', positioning, '0')
        make(doc, 'sweepAngle', positioning, '0')
        make(doc, 'dihedralAngle', positioning, '0')
        make(doc, 'toSectionUID', positioning, Name)

    else:
        # Geometric longitudinal length
        length_val = Sections_parameters[Section_key]['Span'] / (
            np.cos(np.deg2rad(Sections_parameters[Section_key]['Sweep_angle']))
        )
        make(doc, 'length', positioning, str(length_val))

        # Sweep and dihedral values
        sweep_angle = Sections_parameters[Section_key]['Sweep_angle']
        dihedral_angle = Sections_parameters[Section_key].get('Dihedral_angle', 0.0)

        make(doc, 'sweepAngle', positioning, str(sweep_angle))
        make(doc, 'dihedralAngle', positioning, str(float(dihedral_angle) - dih_list[-1]))

        # Connectivity between wing sections
        prev_name = f'{Name[:len(Name) - 1]}{int(Name[-1]) - 1}'
        make(doc, 'fromSectionUID', positioning, prev_name)
        make(doc, 'toSectionUID', positioning, Name)

    # Update dihedral history list
    dih_val = Sections_parameters[Section_key].get('Dihedral_angle', 0.0)
    if Sections_parameters["Transformation"]["Relative_dih"]:
        dih_list.append(dih_val)
    else:
        dih_list.append(0)


def wingAirfoil(doc, Parent, Section_key, Section_parameters, uid):

    # Create wing airfoil element with uID
    wingAirfoil = make(doc, 'wingAirfoil', Parent, uID=str(uid))
    make(doc, 'name', wingAirfoil, str(uid))

    # List of coordinate vectors
    pointList = make(doc, 'pointList', wingAirfoil)

    txt = ['x', 'y', 'z']
    x_values = Section_parameters[Section_key]['Airfoil_coordinates'][0]
    y_values = np.zeros(np.shape(x_values))
    z_values = Section_parameters[Section_key]['Airfoil_coordinates'][1]

    x_cpacs = np.column_stack((x_values, y_values, z_values))

    for tag, elem in enumerate(txt):
        values_str = ' '.join(str(x_cpacs[:, tag]).strip().split()) \
                        .replace('[ ', '').replace('[', '').replace(
                            ' ]', '').replace(']', '').replace(' ', ';')
        child = make(doc, elem, pointList, values_str)
        child.setAttribute('mapType', 'vector')


def Wing_to_CPACS(
    WingData,
    doc,
    Parent_wing,
    Parent_prof,
    name_file,
    output_dir: Path | None = None,
):

    # ---- keys of the dictionary( number of sections, trasformation of the main wing...) ----#
    keys = list(WingData.keys())
    Name_wing = WingData[keys[0]]['Name']

    # <wings>
    wings = make(doc, 'wings', Parent_wing)

    # <wing>
    wing = make(doc, 'wing', wings, uID=Name_wing)
    make(doc, 'name', wing, Name_wing)

    if WingData[keys[0]]['Symmetry'] != '0':
        wing.setAttribute(
            'symmetry', WingData[keys[0]]['Symmetry'])

    # name - description - transformation #
    Transformation(doc, wing, Name_wing, np.ones(
        3).T, np.array(WingData[keys[0]]['X_Rot']),
        WingData[keys[0]]['X_Trasl'], WingData[keys[0]]['abs_system'])

    # <sections>
    Name_section = {}
    Name_element = {}
    Name_airfoil = {}
    sections = make(doc,'sections',wing)

    for Section_key in keys[1:]:

        # <section>f'{Name_wing}Sec{Section_key[-1]}'
        Wing_section(
            doc, sections, Name_wing, Section_key, WingData)

        match = re.search(r'\d+$', Section_key)
        number = int(match.group()) if match else 0

        Name_section[Section_key] = {
            'Name': f'{Name_wing}Sec{number}'
        }
        Name_element[Section_key] = {
            'Name': f"{Name_wing}Sec{number}Elem"
        }
        Name_airfoil[Section_key] = {
            'Name':f"{Name_wing}Sec{number}_{WingData[Section_key]['Airfoil']}"
        }

    # <positioning>
    positionings = make(doc,'positionings',wing)
    dih_list = []
    for Section_key in keys[1:]:
        Wing_positioning(
            doc, positionings, Name_section[Section_key]['Name'], Section_key, WingData, dih_list)

    # <segments>
    segments = make(doc,'segments',wing)
    Name_element_before = None
    for Section_key in keys[1:]:

        match = re.search(r'\d+$', Section_key)
        number = int(match.group()) if match else 0

        if Section_key != 'Section0' and Name_element_before is not None:
            segment(
                doc, segments, Name_wing,
                Name_element[Section_key]['Name'], Name_element_before, number
            )
            Name_element_before = Name_element[Section_key]['Name']
        Name_element_before = Name_element[Section_key]['Name']

    # <profiles>
    profiles = make(doc,'profiles',Parent_prof)
    wingAirfoils = make(doc,'wingAirfoils',profiles)

    for Section_key in keys[1:]:
        wingAirfoil(
            doc, wingAirfoils, Section_key, WingData, Name_airfoil[Section_key]['Name'])

    return Save_CPACS_file(doc, name_file, output_dir)


def Fuselage_to_CPACS(
    FuseData,
    doc,
    Parent_Fuse,
    Parent_prof,
    name_file,
    output_dir: Path | None = None,
):

    # ---- keys of the dictionary( number of sections, trasformation of the fuselage...) ----#
    keys = list(FuseData.keys())
    Fuse_name = FuseData[keys[0]]['Name']
    # <fuselages>
    fuselages = make(doc,'fuselages',Parent_Fuse)

    # <fuselage>
    fuselage = make(doc, 'fuselage', fuselages, uID=Fuse_name)
    make(doc, 'name', fuselage, Fuse_name)

    if FuseData[keys[0]]['Symmetry'] != '0':
        fuselage.setAttribute(
            'symmetry', FuseData[keys[0]]['Symmetry'])

    # name - description - transformation #
    Transformation(doc, fuselage, Fuse_name, np.ones(
        3).T, np.array(FuseData[keys[0]]['X_Rot']),
        FuseData[keys[0]]['X_Trasl'], FuseData[keys[0]]['abs_system'])

    # <sections>
    Name_section = {}
    Name_element = {}
    Name_airfoil = {}
    sections = make(doc,'sections',fuselage)

    for Section_key in keys[1:]:
        # <section>
        Fuse_section(
            doc, sections, Fuse_name, Section_key, FuseData)

        match = re.search(r'\d+$', Section_key)

        number = int(match.group()) if match else 0

        Name_section[Section_key] = {
            'Name': f"{Fuse_name}Sec{number}"
        }
        Name_element[Section_key] = {
            'Name': f"{Fuse_name}Sec{number}Elem"
        }
        Name_airfoil[Section_key] = {
            'Name':f"{Fuse_name}Sec{number}_{FuseData[Section_key]['Airfoil']}"
        }

    # <positioning>
    positionings = make(doc,'positionings',fuselage)

    Store_perc_length = []
    for Section_key in keys[1:]:
        Fuse_positioning(
            doc, positionings,
            Name_section[Section_key]['Name'], Section_key, FuseData, Store_perc_length)

    # <segments>
    segments = make(doc,'segments',fuselage)

    Name_element_before = None
    for Section_key in keys[1:]:

        match = re.search(r'\d+$', Section_key)
        number = int(match.group()) if match else 0

        if Section_key != "Section0" and Name_element_before is not None:
            segment(
                doc,
                segments,
                Fuse_name,
                Name_element[Section_key]["Name"],
                Name_element_before,
                number,
            )

        Name_element_before = Name_element[Section_key]["Name"]

    # <profiles>
    profiles = make(doc,'profiles',Parent_prof)
    fuselageProfiles = make(doc,'fuselageProfiles',profiles)

    for Section_key in keys[1:]:
        Fuse_Profile(
            doc,fuselageProfiles,FuseData, Section_key,Name_airfoil[Section_key]['Name'])
    return Save_CPACS_file(doc, name_file, output_dir)


def Engine_profile(doc, vehicle, data, name, i):
    # Create <profiles> container
    profiles = make(doc, 'profiles', vehicle)

    # <curveProfiles>
    curveProfiles = make(doc, 'curveProfiles', profiles)
    if len(i) == 1:
        curveProfile = make(doc, 'curveProfile', curveProfiles, uID=f"{name}_fanCowlRotationCurve")
        pointList = make(doc, 'pointList', curveProfile)
        make(doc, 'x', pointList, '0;1')
        make(doc, 'y', pointList, '-0.06;-0.06')
    elif len(i) == 2:
        curveProfile = make(doc, 'curveProfile',
                            curveProfiles, uID=f"{name}_coreCowlRotationCurve")
        pointList = make(doc, 'pointList', curveProfile)
        make(doc, 'x', pointList, '0.27108433734939763;0.2720883534136546')
        make(doc, 'y', pointList, '-0.0252;-0.0252')
    elif len(i) == 3:
        curveProfile = make(doc, 'curveProfile',
                            curveProfiles, uID=f"{name}_centerCowlRotationCurve")
        pointList = make(doc, 'pointList', curveProfile)
        cp = " ".join(str(data["Transformation"]["curveProfile"][0]).strip().split())
        cp = cp.replace("[ ", "").replace(
            "[", "").replace(" ]", "").replace("]", "").replace(" ", ";")
        make(doc, "x", pointList, cp)
        cp = " ".join(str(data["Transformation"]["curveProfile"][1]).strip().split())
        cp = cp.replace("[ ", "").replace(
            "[", "").replace(" ]", "").replace("]", "").replace(" ", ";")
        make(doc, "y", pointList, cp)

    # <nacelleProfiles>
    nacelleProfiles = make(doc, 'nacelleProfiles', profiles)
    if len(i) == 1:
        nacelleProfile = make(doc, 'nacelleProfile',
                              nacelleProfiles, uID=f"{name}_Nacelle_fanCowl_{data['Airfoil']}")
        make(doc, 'name', nacelleProfile, data['Airfoil'])
        pointList = make(doc, 'pointList', nacelleProfile)
        coord_x = " ".join(str(data["Airfoil_coordinates"][0]).strip().split())
        coord_x = coord_x.replace("[ ", "").replace("[", "").replace(
            " ]", "").replace("]", "").replace(" ", ";")
        make(doc, "x", pointList, coord_x)
        coord_y = " ".join(str(data["Airfoil_coordinates"][1]).strip().split())
        coord_y = coord_y.replace("[ ", "").replace("[", "").replace(
            " ]", "").replace("]", "").replace(" ", ";")
        make(doc, "y", pointList, coord_y)
    elif len(i) == 2:
        nacelleProfile = make(doc, 'nacelleProfile',
                              nacelleProfiles, uID=f"{name}_Nacelle_coreCowl_{data['Airfoil']}")
        make(doc, 'name', nacelleProfile, data['Airfoil'])
        pointList = make(doc, 'pointList', nacelleProfile)
        coord_x = " ".join(str(data["Airfoil_coordinates"][0]).strip().split())
        coord_x = coord_x.replace("[ ", "").replace(
            "[", "").replace(" ]", "").replace("]", "").replace(" ", ";")
        make(doc, "x", pointList, coord_x)
        coord_y = " ".join(str(data["Airfoil_coordinates"][1]).strip().split())
        coord_y = coord_y.replace("[ ", "").replace("[", "").replace(
            " ]", "").replace("]", "").replace(" ", ";")
        make(doc, "y", pointList, coord_y)


def Engine_to_CPACS(
    EngineData,
    doc,
    Parent_engine,
    Parent_prof,
    i,
    name_file,
    output_dir: Path | None = None,
):
    # ---- keys of the dictionary( number of sections, trasformation of the fuselage...) ----#
    NameEngine = f"""{
        EngineData['Transformation']['Name']
    }_Engine{EngineData['Transformation']['idx_engine']}"""

    if len(i) == 1:
        # <engines>
        engines = make(doc, 'engines', Parent_engine)

        # <engine>
        engine = make(doc, 'engine', engines, uID=f"{NameEngine}_Positioning")
        if EngineData['Transformation']['Symmetry'] != '0':
            engine.setAttribute('symmetry', EngineData['Transformation']['Symmetry'])

        # <parentUID>
        make(doc, 'parentUID', engine, EngineData['Transformation']['Child_to_Parent'])

        # <engineUID>
        make(doc, 'engineUID', engine, NameEngine)

        # Transformation for engine
        Transformation(doc, engine, NameEngine,
                       [1, EngineData['Transformation']['width'],
                        EngineData['Transformation']['height']],
                       EngineData['Transformation']['X_Rot'],
                       EngineData['Transformation']['X_Trasl'])

    # <profiles>
    Engine_profile(doc, Parent_prof, EngineData, NameEngine, i)

    return Save_CPACS_file(doc, name_file, output_dir)


def merge_elements(document, parent_tag, target_tag):

    # unify more element <target_tag> inside the arent node <parent_tag> , only if exist.
    parent_nodes = document.getElementsByTagName(parent_tag)
    if not parent_nodes:
        return document
    parent = parent_nodes[0]
    elements = list(parent.getElementsByTagName(target_tag))
    if not elements:
        return document
    first = elements[0]
    if len(elements) > 1:
        for extra in elements[1:]:
            for c in list(extra.childNodes):
                extra.removeChild(c)
                first.appendChild(c)
            extra.parentNode.removeChild(extra)
    return document


def Save_CPACS_file(Document, name_file, output_dir: Path | None = None) -> Path:

    merge_elements(Document, 'model', 'wings')
    merge_elements(Document, 'model', 'fuselages')
    merge_elements(Document, 'vehicles', 'profiles')
    merge_elements(Document, 'profiles', 'fuselageProfiles')
    merge_elements(Document, 'profiles', 'wingAirfoils')
    merge_elements(Document,'profiles','curveProfiles')
    merge_elements(Document,'profiles','nacelleProfiles')

    xml_str = Document.toprettyxml(indent="  ")

    # The file will be saved either in the provided output directory or, by default,
    # in the same folder as this module.
    if output_dir is None:
        module_dir = Path(__file__).parent
        output_dir = module_dir.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f'{name_file}.xml'

    with open(output_path, 'w') as xml_file:
        xml_file.write(xml_str)

    return output_path


# Classes
class _ETElement:
    def __init__(self, element, parent: "_ETElement | None" = None):
        self._element = element
        self._parent = parent

    @property
    def parentNode(self) -> "_ETElement | None":
        return self._parent

    @property
    def childNodes(self) -> list["_ETElement"]:
        return [_ETElement(child, parent=self) for child in list(self._element)]

    def setAttribute(self, key: str, value: str) -> None:
        self._element.set(key, value)

    def appendChild(self, node):
        if isinstance(node, str):
            text_value = str(node)
            if self._element.text is None:
                self._element.text = text_value
            else:
                self._element.text += text_value
            return node
        if isinstance(node, _ETElement):
            self._element.append(node._element)
            node._parent = self
            return node
        raise TypeError(f"Unsupported node type for appendChild: {type(node)!r}")

    def removeChild(self, node: "_ETElement"):
        if not isinstance(node, _ETElement):
            raise TypeError(f"Unsupported node type for removeChild: {type(node)!r}")
        self._element.remove(node._element)
        node._parent = None
        return node

    def getElementsByTagName(self, tag: str) -> list["_ETElement"]:
        matches: list[_ETElement] = []

        def walk(element, parent_wrapper: _ETElement) -> None:
            for child in list(element):
                child_wrapper = _ETElement(child, parent=parent_wrapper)
                if child.tag == tag:
                    matches.append(child_wrapper)
                walk(child, child_wrapper)

        walk(self._element, self)
        return matches


class _ETDocument:
    def __init__(self):
        self._root: _ETElement | None = None

    def createElement(self, name: str) -> _ETElement:
        return _ETElement(ET.Element(name))

    def createTextNode(self, value: str) -> str:
        return str(value)

    def appendChild(self, node: _ETElement) -> _ETElement:
        if self._root is not None:
            raise ValueError("Document already has a root element")
        self._root = node
        return node

    def getElementsByTagName(self, tag: str) -> list[_ETElement]:
        if self._root is None:
            return []
        if self._root._element.tag == tag:
            return [self._root, *self._root.getElementsByTagName(tag)]
        return self._root.getElementsByTagName(tag)

    def toprettyxml(self, indent: str = "  ") -> str:
        if self._root is None:
            return ""
        ET.indent(self._root._element, space=indent)
        return ET.tostring(self._root._element, encoding="unicode", xml_declaration=True)


class Export_CPACS:
    def __init__(self, Data, name_file, output_dir: Path | None = None):
        self.Data = Data
        self.name_file = name_file
        self.output_dir = output_dir
        self.output_path: Path | None = None

    def run(self) -> Path:
        # Create the document
        Doc = _ETDocument()

        # find the keys
        keys = list(self.Data.keys())

        # dummy variable for the engine
        dummy_idx_engine = []

        # CPACS's initialization
        Doc, model, vehicles = initialization(Doc, self.Data, self.name_file)

        # Loop to connect the components inside the CPACS
        for item in keys:
            log.info(f"Component {item} {self.Data[f'{item}']['Transformation']['Name_type']} ")
            if self.Data[f'{item}']['Transformation']['Name_type'] == 'Wing':
                self.output_path = Wing_to_CPACS(
                    self.Data[f'{item}'],
                    Doc,
                    model,
                    vehicles,
                    self.name_file,
                    self.output_dir,
                )
            if self.Data[f'{item}']['Transformation']['Name_type'] == 'Fuselage':
                self.output_path = Fuselage_to_CPACS(
                    self.Data[f'{item}'],
                    Doc,
                    model,
                    vehicles,
                    self.name_file,
                    self.output_dir,
                )
            if (
                self.Data[f'{item}']['Transformation']['Name_type'] == 'Pod'
                and self.Data[f'{item}']['Transformation']['idx_engine'] is None
            ):
                self.output_path = Fuselage_to_CPACS(
                    self.Data[f'{item}'],
                    Doc,
                    model,
                    vehicles,
                    self.name_file,
                    self.output_dir,
                )
            if (
                self.Data[f'{item}']['Transformation']['Name_type'] == 'Duct'
                or self.Data[f'{item}']['Transformation']['idx_engine'] is not None
            ):
                if len(dummy_idx_engine) < 3:
                    dummy_idx_engine.append(
                        self.Data[f'{item}']['Transformation']['idx_engine']
                    )
                self.output_path = Engine_to_CPACS(
                    self.Data[f'{item}'],
                    Doc,
                    model,
                    vehicles,
                    dummy_idx_engine,
                    self.name_file,
                    self.output_dir,
                )

        if self.output_path is None:
            raise RuntimeError("Failed to export CPACS file from OpenVSP geometry.")

        return self.output_path
