# DirectX bytecode to pica200 assembly converter

[!WARNING]
Uniforms are not declared due to how picasso allocates declared registers, so you need to use the register IDs directly

Currently experimental, generally functional enough to be used on simple shaders. 

Currently mostly supports up to vs3_0 with some important differences:
- cmp register has 2 components instead of 4, so programs using more will not compile
- a0 register has 2 components instead of 4, so programs using more will not compile
- Certain macro functions aren't supported such as `sincos` and `crs`
- Some rounding behaviour, for example with `mova`, is different

### Main fixes that this applies:
- Fixes when uniforms are used in invalid source operand positions
- Note: this may create a larger program, up to 2 extra instructions per input instruction in some cases
- Fixes register names
- Converts some macros to actual instructions when possible

### Usage:
```
python3 converter.py [-i, --input INPUT] [-o, --output OUTPUT]
```
If an input is not specified, will use stdin, and if output is not specified will use stdout.