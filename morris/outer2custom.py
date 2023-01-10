import sys
import os
import shutil
import xml.etree.ElementTree as ET
import pandas as pd


def outer2custom(xml_pth, csv_pth):
    df = pd.read_csv(csv_pth)
    custom_sampling_vars = list(df.columns)[:-2]

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
        if child.get('name') in custom_sampling_vars or child.tag == 'variable':
            custom_sampler.append(ET.Element('variable', {'name': child.get('name')}))
        elif child.tag == 'constant':
            custom_sampler.append(child)
    # Add <CustomSampler> and delete <Grid>
    if 'random_seed' in df:
        custom_sampler.append(ET.Element('variable', {'name': 'random_seed'}))
        code = root.find('.//Code[@name="raven"]')
        seed_alias = ET.Element('alias', {'variable': 'random_seed', 'type': 'input'})
        seed_alias.text = 'Samplers|MonteCarlo@name:mc_arma_dispatch|constant@name:random_seed'
        code.append(seed_alias)

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
    shutil.copy2(xml_pth, xml_pth + '.backup')
    tree.write(xml_pth)


if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        assert os.path.exists(filepath)
    outer_path = sys.argv[1]
    csv_path = sys.argv[2]
    outer2custom(outer_path, csv_path)

