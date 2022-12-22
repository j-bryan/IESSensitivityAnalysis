import sys
import os
import xml.etree.ElementTree as ET


def outer2custom(xml_pth, csv_pth):
    tree = ET.parse(xml_pth)
    root = tree.getroot()
    
    # Edit existing <Sampler> node in <Steps> to be:
    # <Sampler class="Samplers" type="CustomSampler">customSampler</Sampler>
    sampler_step = root.find('./Steps/MultiRun/Sampler')
    sampler_step.set('type','CustomSampler')
    sampler_step.text = 'customSampler'

    # Find <Samplers> node
    samplers = root.find('Samplers')
    # Create <CustomSampler name="customSampler"> subnode
    custom_sampler = ET.Element('CustomSampler', {'name': 'customSampler'})
    # Add <Source> node to <CustomSampler>
    source = ET.Element('Source', {'class': 'Files', 'type': ''})
    source.text = 'samples'
    custom_sampler.append(source)
    # Find <Grid> subnode
    grid_sampler = samplers.find('Grid')
    # Copy all <constant> subsubnodes from <Grid> to <CustomSampler>
    for child in grid_sampler:
        if child.tag == 'constant':
            custom_sampler.append(child)
        elif child.tag == 'variable':
            custom_sampler.append(ET.Element('variable', {'name': child.get('name')}))
    # Add <CustomSampler> and delete <Grid>
    samplers.append(custom_sampler)
    samplers.remove(grid_sampler)

    # Find <Files> node
    files = root.find('Files')
    # Add <Input name="samples">../$csv_pth</Input> to <Files>
    csv_node = ET.Element('Input', {'name': 'samples'})
    csv_node.text = os.path.join('..', csv_pth)
    files.append(csv_node)

    # Write edited XML to file
    #with open('outer_custom.xml', 'w') as f:
    #    tree.write(f)
    tree.write('outer_custom.xml')


if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        assert os.path.exists(filepath)
    outer_path = sys.argv[1]
    csv_path = sys.argv[2]
    outer2custom(outer_path, csv_path)

