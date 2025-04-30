#! /bin/bash
#
# Collect boost dependencies 

cd
rm -rf $HOME/tmp/bcp
mkdir -p $HOME/tmp/bcp

for i in genua surf scope sumo dwfs dwfs-2 phi lsfem ludwig vzm/app vzm/yaobi s2dof
do
  f=$HOME/Develop/$i
  bcp --boost=$HOME/Software/boost_1_57_0 --scan $f/*.h $f/*.cpp $HOME/tmp/bcp
done

find $HOME/tmp/bcp/libs -name "build" -o -name "test" | xargs rm -rf
