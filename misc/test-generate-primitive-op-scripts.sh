mkdir -p /tmp/workspace
python3.9 -m athena.tool.primitive_op_scripts --ir_programs=./primitive-op-input/original_programs.py --example_inputs=./primitive-op-input/programs_example_input_tensor_meta.py --workspace_dir=/tmp/workspace
