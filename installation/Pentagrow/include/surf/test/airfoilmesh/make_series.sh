#! /bin/bash
#
# generate a series of meshes

refine=0.7
alpha=(-1 1 3 5 7 9 11)
dname=(-4 +0 +8 +14)
af=ed36f128
afroot=$HOME"/Project/umtaps/airfoil/"$af

for i in ${alpha[@]}; do
  for j in ${dname[@]}; do
    srcfile=$afroot$j".dat"
    dstfile="l2k-a"$i"-"$af$j"-n20k.zml" 
    echo $srcfile $dstfile
    ./airfoilmesh $srcfile $refine $i
    mv tetmesh2.zml $dstfile
  done
done

