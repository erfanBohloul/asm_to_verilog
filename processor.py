import xml.etree.ElementTree as ET
from collections import defaultdict

def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    asm_data = {
        'name': root.get('name', 'asm_fsm'),
        'inputs': [],
        'outputs': [],
        'variables': [],
        'states': {},
        'decisions': {},
        'conditionals': {},
        'transitions': []
    }

    vars_elem = root.find('variables')
    if vars_elem is not None:
        for var in vars_elem.findall('variable'):
            var_type = var.get('type', None)
            if var_type == 'input':
                asm_data['inputs'].append((var.get('id'), var.get('datatype', "reg"), var.get("bitwidth", 1)))
            elif var_type == 'output':
                asm_data['outputs'].append((var.get('id'), var.get('datatype', "reg"), var.get("bitwidth", 1)))
            elif var_type == 'inout':
                pass
            else:
                asm_data['variables'].append((var.get('id'), var.get('datatype', "reg"), var.get("bitwidth", 1)))


    states_elem = root.find('states')
    if states_elem is not None:
        for state in states_elem.findall('state'):
            state_id = state.get('id')
            asm_data['states'][state_id] = {
                'instructions': parse_instructions(state.find('instructions'))
            }


    decisions_elem = root.find('decisions')
    if decisions_elem is not None:
        for decision in decisions_elem.findall('decision'):
            decision_id = decision.get('id')
            asm_data['decisions'][decision_id] = {
                'condition': decision.get('condition')
            }
    
    
    cond_outputs_elem = root.find('conditionals')
    if cond_outputs_elem is not None:
        for co in cond_outputs_elem.findall('conditional'):
            co_id = co.get('id')
            asm_data['conditionals'][co_id] = {
                'instructions': parse_instructions(co.find('instructions'))
            }

        
    transitions_elem = root.find('transitions')
    if transitions_elem is not None:
        for trans in transitions_elem.findall('transition'):
            asm_data['transitions'].append({
                'from': trans.get('from'),
                'to': trans.get('to'),
                'when': trans.get('when', None)  # Only for decision transitions
            })

    return asm_data

def parse_instructions(instructions_elem):
    if instructions_elem is None:
        return []
    
    instructions = []
    for instr in instructions_elem:
        if instr.tag == 'assign':
            instructions.append({
                'type': 'assign',
                'target': instr.get('target'),
                'value': instr.get('value', None),
                'expr': instr.get('expr', None)
            })

        elif instr.tag == 'print':
            vars = [var.text for var in instr.findall('var')]
            instructions.append({
                'type': 'print',
                'format': instr.get('format'),
                'vars': vars
            })

    
    return instructions

def build_transition_graph(asm_data):
    graph = defaultdict(list)

    for trans in asm_data['transitions']:
        from_node = trans['from']
        to_node = trans['to']

        if trans['when'] is not None:
            
            condition = asm_data['decisions'][from_node]['condition']
            if trans['when'] == 'false':
                condition = f'!({condition})'
            graph[from_node].append((to_node, condition))
        else:
            graph[from_node].append((to_node, True))



    return graph

def process_asm(xml_file):
    asm_data = parse_xml(xml_file)
    transition_graph = build_transition_graph(asm_data)

    return {
        'asm_data': asm_data,
        'transition_graph': transition_graph
    }

