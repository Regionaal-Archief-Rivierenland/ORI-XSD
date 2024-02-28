import yaml
# needed because descriptions might contain html
from markdownify import markdownify as md
import xml.etree.ElementTree as ET
import re

f_xsd = "ORI.xsd"
xsd_ns = 'https://www.w3.org/2001/XMLSchema'
ns = {"xsd" : xsd_ns}
# https://stackoverflow.com/questions/18338807/cannot-write-xml-file-with-default-namespace
ET.register_namespace('xsd', xsd_ns)

tree = ET.parse(f_xsd)
xsd_root = tree.getroot()

# read json
with open("openapi.yaml") as yf:
    yaml_data = yaml.safe_load(yf)

element_names = [e.attrib['name'] for e in xsd_root.findall(".//xsd:element", ns)]

def find_descriptions_for_element(target_element, yaml_data):
    """recursively traverse dictionary, searching for an element's descriptions"""

    descriptions = []
    
    if isinstance(yaml_data, dict):
        for key, value in yaml_data.items():
            # base case
            if str(key).lower() == target_element.lower():
                description = find_description(value)
                if description:
                    descriptions.append(description)
            # traverse deeper
            # extend is the same as append but works on iterables
            descriptions.extend(find_descriptions_for_element(target_element, value))

    elif isinstance(yaml_data, list):
        # traverse list
        for item in yaml_data:
            descriptions.extend(find_descriptions_for_element(target_element, item))

    return descriptions

def find_description(yaml_data):
    if isinstance(yaml_data, dict):
        for key, value in yaml_data.items():
            # base case
            if key == 'description':
                return value
            else:
                # go deeper
                result = find_description(value)
                if result:
                    return result

    elif isinstance(yaml_data, list):
        for item in yaml_data:
            result = find_description(item)
            if result:
                return result

elem_descriptions = {}

for e in element_names:
    elem_descriptions[e] = find_descriptions_for_element(e, yaml_data)

complexTypes = xsd_root.findall(".//xsd:complexType", ns)
for ct in complexTypes:
    ct_name = ct.attrib['name']
    for e in ct.findall(".//xsd:element", ns):
        e_name = e.attrib['name']
        descriptions = list(set(elem_descriptions[e_name]))

        if len(descriptions) == 0:
            print(f"No description found for {ct_name}>{e_name}")
            description = "TODO"
        elif len(descriptions) > 1:
            print(f"Descriptions for {ct_name}>{e_name}")
            choices = [(i, d) for i, d in enumerate(descriptions)]
            choices.append((len(choices), "TODO"))
            descriptions.append("TODO")
            print(choices)
            # default answer is 0
            try:
                idx = int(input("Pick description [idx]: "))
            except:
                idx = 0 
            description = descriptions[idx]
        else:
            description = descriptions[0]
        
        # capitalize and add period
        if description != "TODO":
            description = description[0].upper() + description[1:] + ('' if description.endswith('.') else '.')
            description = description.replace('\n', ' ')
            # replace ALLCAPS words
            to_lowercase = lambda matchobj: "`" + matchobj.group(0).lower() + "`"
            description = re.sub(r"\b[A-Z]+\b", to_lowercase, description)

        # markdownify
        description = md(description, escape_underscores=False, escape_asterisks=False)
        annotation = ET.Element(f'{{{xsd_ns}}}annotation')
        doc_xml = ET.Element(f'{{{xsd_ns}}}documentation')
        doc_xml.text = description

        annotation.append(doc_xml)
        e.append(annotation)


ET.indent(tree, space="	") # indent with tab
tree.write('/tmp/ORI-doc.xsd', xml_declaration=True, encoding='utf-8')
