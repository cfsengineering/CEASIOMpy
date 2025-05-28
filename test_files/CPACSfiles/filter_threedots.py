import xml.etree.ElementTree as ET

def replace_threedots_with_uid(xml_path, output_path=None):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Helper to find parent (since ElementTree does not provide it)
    def find_parent(root, child):
        for parent in root.iter():
            for elem in parent:
                if elem is child:
                    return parent
        return None

    for name_elem in root.iter('name'):
        if name_elem.text == "threedots":
            parent = find_parent(root, name_elem)
            if parent is not None:
                uid = parent.attrib.get("uID")
                if uid:
                    name_elem.text = uid

    if output_path is None:
        output_path = xml_path
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python replace_threedots.py input.xml [output.xml]")
        sys.exit(1)
    xml_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    replace_threedots_with_uid(xml_path, output_path)