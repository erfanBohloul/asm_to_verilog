

def generate_verilog(processed_data, initial_state="s0"):
    asm_data = processed_data['asm_data']
    transition_graph = processed_data['transition_graph']

    states = asm_data['states']
    decisions = asm_data['decisions']
    conditionals = asm_data['conditionals']
    variables = asm_data['variables']
    inputs = asm_data['inputs']
    outputs = asm_data['outputs']

    verilog = []
    verilog += generate_args(asm_data['name'], inputs, outputs)
    verilog += define_vars(variables)
    verilog += generate_state_vars(states.keys(), initial_state)
    verilog += clock_transition()
    verilog += next_state_logic(states.keys(), transition_graph)

    verilog.append("    always @(posedge clk) begin")
    # verilog += default_assignment(variables, outputs)

    
    verilog.append("        case (current_state)")
    for state in asm_data['states']:
        verilog.append(f"            {state}: begin")
        verilog += ["\t\t" + line for line in conditional_logic(state, states, conditionals, decisions, transition_graph)]
        verilog.append("            end")
    verilog.append("        endcase")
    verilog.append("    end")
    verilog.append("")

    verilog.append("endmodule")
    verilog.append("")
    return verilog

def conditional_logic(component, states, conditions, desicions, transition_graph):
    transition = transition_graph.get(component, [])
    verilog = []

    if component in states:
        instructions = states[component]['instructions']
        for instruction in instructions:
            verilog.append(f"   {instruction_to_verilog(instruction)};")

        to_state = transition[0][0]
        if to_state in states:
            return verilog
        
        verilog += conditional_logic(to_state, states, conditions, desicions, transition_graph)

    elif component in conditions:
        instructions = conditions[component]['instructions']
        for instruction in instructions:
            verilog.append(f"   {instruction_to_verilog(instruction)};")

        to_state = transition[0][0]
        if to_state in states:
            return verilog
        verilog += conditional_logic(to_state, states, conditions, desicions, transition_graph)
    
    elif component in desicions:
        true_component = transition[0][0]
        false_component = transition[1][0]
        cond = transition[0][1]


        verilog.append(f"if ({cond}) begin")

        if true_component not in states:
            verilog += conditional_logic(true_component, states, conditions, desicions, transition_graph)
        verilog.append("end")

        if false_component not in states:
            verilog.append("else begin")
            verilog += conditional_logic(false_component, states, conditions, desicions, transition_graph)
            verilog.append("end")
    
    else:
        raise ValueError(f"Component {component} not found in states, conditions, or decisions.")

        
    return ["\t" + line for line in verilog]  # Add a new line after each instruction
        
def instruction_to_verilog(instruction):
    type = instruction.get('type')

    if type == 'assign':
        target = instruction.get('target')
        value = instruction.get('value')
        return f"{target} <= {value}"
    
    elif type == 'print':
        format_str = instruction.get('format').replace('"', '\\"')
        vars = instruction.get('vars', [])
        display_vars = ", ".join(vars)
        if not display_vars:
            return f'$display("{format_str}")'
        return f'$display("{format_str}", {display_vars})'
    
    return "UNKNOWN INSTRUCTION"

# def default_assignment(variables, outputs):
#     verilog = []
#     verilog.append("        // Default assignments")

#     for var in variables + outputs:
#         name, dtype, bit_width = var
#         bit_width = int(bit_width)

#         default = f"{bit_width}'b0" if bit_width > 1 else "1'b0"
#         verilog.append(f"        {name} = {default};")
#     verilog.append("")
#     return verilog
    
def next_state_logic(states, transition_graph):
    verilog = []
    verilog.append("    always @(*) begin")
    verilog.append("        case (current_state)")

    for state in states:
        verilog.append(f"            {state}: begin")
        next_states = get_next_states(state, True, states, transition_graph)
        if not next_states:
            verilog.append("                next_state = current_state; // No transition")
        else:
            for target, condition in next_states:
                if condition is True:
                    verilog.append(f"                next_state = {target};")
                else:
                    verilog.append(f"                if ({condition}) next_state = {target};")

        verilog.append("            end")

    verilog.append("        endcase")
    verilog.append("    end")
    verilog.append("")
    return verilog

def get_next_states(component, condition, states, transition_graph):
    
    ans = []
    transition = transition_graph.get(component, [])
    for target, cond in transition:
        
        if cond == True:
            new_condition = condition
        else:
            new_condition = f"({cond})" if (condition == True) else f"{condition} && ({cond})"


        if target in states:
            ans += [(target, new_condition)]
        else:
            ans += get_next_states(target, new_condition, states, transition_graph)

    return ans

def clock_transition():
    return [
        "    always @(posedge clk) begin",
        "        current_state <= next_state;",
        "    end",
        ""
    ]

def generate_state_vars(states, initial_state):
    verilog = []
    verilog.append("    // State definitions")
    verilog.append("    localparam")
    state_params = []

    for i, state in enumerate(states):
        state_params.append(f"    {state} = {i},")
    state_params[-1] = state_params[-1][:-1]  # Remove the last comma
    verilog.append("\n".join(state_params) + ";")
    verilog.append("")

    state_width = max(1, (len(states) -1).bit_length())
    verilog.append(f"    reg [{state_width-1}:0] current_state = {initial_state};\n    reg [{state_width-1}:0] next_state;")
    verilog.append("")
    
    return verilog

def generate_args(asm_name, inputs, outputs):
    args = [
        f"module {asm_name} (",
        "    input wire clk,",
        
    ]

    for inp in inputs:
        name, dtype, bit_width = inp
        bit_width = int(bit_width)
        args.append(f"    input {dtype} [{bit_width-1}:0] {name},")
    
    for out in outputs:
        name, dtype, bit_width = out
        bit_width = int(bit_width)
        args.append(f"    output {dtype} [{bit_width-1}:0] {name},")

    
    # close arg list
    args[-1] = args[-1][:-1] + ");"  # Remove the last comma and add closing parenthesis
    args.append("")

    return args

def define_vars(variables):
    var_defs = []
    for var in variables:
        name, dtype, bit_width = var
        bit_width = int(bit_width)
        var_defs.append(f"    {dtype} [{bit_width-1}:0] {name};")

    var_defs.append("")
    return var_defs


