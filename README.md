# DirectX bytecode to pica200 assembly converter

> [!WARNING]
> Uniforms are declared but may not be accurate due to how picasso allocates declared registers, so you need to use the register IDs directly to be safe.

Currently experimental, generally functional enough to be used on simple shaders. 

## Usage:
```sh
python3 converter.py [-i, --input INPUT] [-o, --output OUTPUT]
```
If an input is not specified, will use stdin, and if output is not specified will use stdout.

Example using stdin:
```sh
$ fxc.exe /nologo /T vs_1_1 /E main input.hlsl | python3 converter.py -o out.v.pica
$ picasso -o out.shbin out.v.pica
```

## Supported versions:
- [X] vs\_1_1
- [X] vs\_2_0
- [X] vs\_2_x
- [X] vs\_3_0
- [ ] vs\_4_0
- [ ] vs\_5_0
- [ ] vs\_5_1
- [ ] gs\_4_0
- [ ] gs\_4_1
- [ ] gs\_5_0
- [ ] gs\_5_1

Currently mostly supports up to vs_3_0 with some important differences:
### vs_3_0 specific:
- cmp register has 2 components instead 4 (applies to vs_2_0+)
- a0 register has 2 components instead of 4 (applies to vs_2_0+)
- Only 96 uniforms are available instead of 256 (applies to vs_2_0+)
- Only 16 scratch registers are available instead of 32
- Texture samplers are not available
- Output type `view` (used for vertex view vector) is not an HLSL semantic so `TANGENT` is used as a stand-in (unavailable outside of vs_3_0)
- The pica200 expects the normal vector output to be a quaternion instead of a vector
### General differences:
- Certain macro functions aren't supported such as `sincos` and `crs`
- texcoord0w does not exist in HLSL, so texcoord3.x is used instead
- Some rounding behaviour, for example with `mova`, is different
- The `lit` instruction isn't currently supported as I'm not entirely sure of the implementation
- HLSL matrices are column-major by default, but C3D is not. You need to specify `row_major` on all matrices in your HLSL code. (After further testing I actually have no idea what's going on with matrices, play around with the attributes until matrix multiplication uses `dp3/4` instead of `mad` which should give the correct result)

## Main fixes that this applies:
- Fixes when uniforms are used in invalid source operand positions
> [!NOTE]
> This may create a larger program, up to 5 extra instructions per input instruction in some cases (working on reducing this)
- Fixes register names to match picasso
- Expands macros when possible

## Planned Features:
- Geometry shader support
- Support for vs\_4_0+ which use fairly different formatting
- Generating SHBIN files directly instead of going through picasso
- Fixing the testing suite

## Credits:
- nightchild for pointing out how similar dx9 bytecode is to pica200 assembly
- tgjones for Shader Playground which allowed me to compile HLSL on linux more easily

>[!NOTE]
>The Microsoft `fxc` compiler outputs some extra info at the start of the file which should be removed before running the converter (or by using the /nologo option).
