import numpy as np
import paddle
import sys
import random

def InitTensorShape(old_value, tensor):
    if old_value is not None:
        return old_value
    if isinstance(tensor, list):
        return [InitTensorShape(None, t) for t in tensor]
    return tensor.shape

def InitTensorData(old_value, tensor):
    if old_value is not None:
        return old_value
    if isinstance(tensor, list):
        return [InitTensorData(None, t) for t in tensor]
    kLimit = 32
    if tensor.numel().item() >= kLimit:
        return None
    ndarray = tensor.numpy()
    if not IsInteger(ndarray.dtype):
        return None
    return ndarray.tolist()

def IsInteger(dtype):
    return np.dtype(dtype).char in np.typecodes['AllInteger']


{%- macro op_input_shape_global_var_name(op_id, input_idx) -%}
op_{{op_id}}_in{{input_idx}}_shape
{%- endmacro %}

{%- macro op_input_data_global_var_name(op_id, input_idx) -%}
op_{{op_id}}_in{{input_idx}}_data
{%- endmacro %}

{% for block in blocks %}
{% for stmt in block.stmts %}
{%- for input_tensor_name in stmt.input_tensor_names %}
{%- set input_idx = loop.index0 %}
{{op_input_shape_global_var_name(stmt.op_id, input_idx)}} = None
{{op_input_data_global_var_name(stmt.op_id, input_idx)}} = None
{%- endfor %}
{%- endfor %}
{%- endfor %}

class OpInputShapesExtractor:
{%- for block in blocks %}
{%- set block_idx = loop.index0 %}

    def {{block.block_name}}(self, {{block.input_arg_names | join(", ")}}):
        
    {%- for stmt in block.stmts %}
        {%- if (stmt.pycode | length) > 0%}

        # {{stmt.op_name}}: ({{stmt.outputs_type_strs|join(", ")}}) <- ({{stmt.inputs_type_strs|join(", ")}})
        {%- for input_tensor_name in stmt.input_tensor_names %}
        {%- set input_idx = loop.index0 %}
        global {{op_input_shape_global_var_name(stmt.op_id, input_idx)}}
        {{op_input_shape_global_var_name(stmt.op_id, input_idx)}} = InitTensorShape(
            {{op_input_shape_global_var_name(stmt.op_id, input_idx)}},
            {{input_tensor_name}}
        )
        global {{op_input_data_global_var_name(stmt.op_id, input_idx)}}
        {{op_input_data_global_var_name(stmt.op_id, input_idx)}} = InitTensorData(
            {{op_input_data_global_var_name(stmt.op_id, input_idx)}},
            {{input_tensor_name}}
        )
        {%- endfor %}
        {%- endif %}
        {%- for pycode in stmt.pycode %}
        {%- if pycode.num_tabs == 0 %}
        {{pycode.pycode}}
        {%- elif pycode.num_tabs == 1 %}
            {{pycode.pycode}}
        {%- elif pycode.num_tabs == 2 %}
                {{pycode.pycode}}
        {%- else %}
        raise NotImplementedError("unsupported indent size {{pycode.num_tabs}}")
        {%- endif %}
        {%- endfor %}
    {%- endfor %}
        return {{block.output_arg_names | join(", ")}}
{%- endfor %}

{% macro get_input_shape_instance(block, block_idx, input_idx) -%}
    {{block.input_tensor_descs[input_idx].shape}}
{%- endmacro %}

{% macro get_input_tensor_instance(block, block_idx, input_idx) -%}
{%- set shape = get_input_shape_instance(block, block_idx, input_idx) -%}
{%- set dtype = block.input_tensor_descs[input_idx].dtype -%}
{%- set big_dtype = block.input_tensor_descs[input_idx].big_dtype -%}
{%- set data = block.input_tensor_descs[input_idx].data -%}
{%- set min = block.input_tensor_descs[input_idx].min -%}
{%- set max = block.input_tensor_descs[input_idx].max -%}
{%- if data != None -%}
    paddle.to_tensor({{data}}, dtype='{{dtype}}').reshape({{shape}})
{%- elif big_dtype == "bool" -%}
    paddle.zeros({{shape}}, dtype='{{dtype}}')
{%- elif big_dtype == "int64" -%}
    paddle.randint(low={{min}}, high={{max}}, shape={{shape}}, dtype='{{dtype}}')
{%- elif big_dtype == "float64" -%}
    paddle.uniform({{shape}}, dtype='{{dtype}}', min={{min}}, max={{max}})
{%- endif -%}
{%- endmacro -%}

def InferBlockInputShapes():
    extractor = OpInputShapesExtractor()
    for _ in range(10):
    {%- for block in blocks %}
    {%- if block.is_entry_block %}
    {%- set block_idx = loop.index0 %}
        extractor.{{block.block_name}}(
        {%- for arg_name in block.input_arg_names %}
        {%- set input_idx = loop.index0 %}
            {{arg_name}}={{get_input_tensor_instance(block, block_idx, input_idx)}},
        {%- endfor %}
        )
    {%- endif %}
    {%- endfor %}

def GetContent():
    return f"""
{% for block in blocks %}
{% for stmt in block.stmts %}
{%- for input_tensor_name in stmt.input_tensor_names %}
{%- set input_idx = loop.index0 %}

class PirProgram_op_input_tensor_meta_{random.randint(0, sys.maxsize)}:
    program_id = {{program_id}}
    op_id = {{stmt.op_id}}
    input_idx = {{input_idx}}
    shape = {str({{op_input_shape_global_var_name(stmt.op_id, input_idx)}})}
    data = {str({{op_input_data_global_var_name(stmt.op_id, input_idx)}})}
{%- endfor %}
{%- endfor %}
{%- endfor %}
"""

if __name__ == '__main__':
    InferBlockInputShapes()
    content = GetContent()
    with open(sys.argv[1], 'w') as f:
        f.write(content)
    print(content)