# CLONE repo:
==============================================
git clone https://gem5.googlesource.com/public/gem5

# Configure and Build RISCV:
==============================================
/usr/bin/env python3 $(which scons) build/RISCV/gem5.opt -j 4

# Run GEM5:
==============================================
./build/RISCV/gem5.opt configs/example/se.py --cpu-type=DerivO3CPU --caches --mem-type=DDR4_2400_8x8 --mem-size=8GB --cmd=/home/saqib/riscV_code/riscv/benchmark_tests/bit_count --options="20" --output=sim.out --errout=sim.err | tee run.out

result will be stored in m5out directory


# More information can be found here:
==============================================
https://vlsiarch.ecen.okstate.edu/gem5/
https://www.gem5.org/documentation/general_docs/building
