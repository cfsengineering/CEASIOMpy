#! /bin/bash
#
# Image preprocessing

for i in $@; do
    bn=$(basename $i .png)
    b2x=$bn"@2x.png"
    pngcrush $i $b2x
    convert $i -scale 50% tmp.png
    rm -f $i
    pngcrush tmp.png $i
    rm -f tmp.png
done