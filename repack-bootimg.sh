#!/bin/bash
# ox0spy <ox0spy@gmail.com>
# 杀鸡焉用牛刀 ... bash简单明了

usage="$0 <kernel> <ramdisk-directory> <outfile>"

if [ $# -ne 3 ]; then
	echo $usage && exit
else
	kernel="$1"
	ramdisk_dir="$2"
	outfile="$3"
fi

cmdline='console=ttyMSM1,115200n8 androidboot.hardware=qcom'
#cmdline='no_console_suspend=1 console=null'

cur_dir=$(pwd)
ramdisk_cpio_gz=$(mktemp)

cd $ramdisk_dir &&
	$(find . | cpio -o -H newc | gzip > $ramdisk_cpio_gz);

cd $cur_dir &&
	$(mkbootimg --cmdline "$cmdline" \
	--kernel $kernel --ramdisk $ramdisk_cpio_gz -o $outfile)

rm -f $ramdisk_cpio_gz

echo "repacked boot image written at $outfile"
