# DirectX bytecode to pica200 assembly converter

> [!CAUTION]
> Please don't use this tool at the moment, as due to a lot of compiler shenanigans it's unlikely to give decent output.
> It will produce code that assembles, but 99% of the time will not work and WILL require manually fixing. 
> I have a few plans to try and fix this, such as adding data flow analysis to the tool but ultimately it will still produce suboptimal code because the compiler just isn't really built for this platform to begin with and all the hacks I have to pull just make it worse.
> At some point I plan to just outright make an HLSL compiler, but until then I suggest either using this for a baseline but writing your own assembly, or just flat out not using this tool at all.

> [!WARNING]
> Uniforms are not declared due to how picasso allocates declared registers, so you need to use the register IDs directly.

Currently experimental, generally functional enough to be used on simple shaders. 

Currently mostly supports up to vs3_0 with some important differences:
- cmp register has 2 components instead of 4, so programs using more will not compile
- a0 register has 2 components instead of 4, so programs using more will not compile
- Certain macro functions aren't supported such as `sincos` and `crs`
- Some rounding behaviour, for example with `mova`, is different
- HLSL matrices are column-major by default, but C3D is not. You need to specify `row_major` on all matrices in your HLSL code.

### Main fixes that this applies:
- Fixes when uniforms are used in invalid source operand positions
> [!NOTE]
> This may create a larger program, up to 4 extra instructions per input instruction in some cases
- Fixes register names
- Expands macros when possible

### Credits:
- nightchild for pointing out how similar dx9 bytecode is to pica200 assembly
- tgjones for Shader Playground which allowed me to compile HLSL on linux easily

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

>[!NOTE]
>The Microsoft `fxc` compiler outputs some extra info at the start of the file which should be removed before running the converter.
>At the moment any unknown lines simply get commented out but is planned to handle it better for the future.
