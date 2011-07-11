#!/usr/bin/env python
# -*- coding: utf-8 -*-
######################################################################
#
#   File          : split_bootimg.py
#   Author(s)     : ox0spy <ox0spy@gmail.com>
#   Description   : Just rewrite William Enck's tools by Python
#                   Split appart an Android boot image created 
#                   with mkbootimg. The format can be found in
#                   android-src/system/core/mkbootimg/bootimg.h
#
#                   Thanks to alansj on xda-developers.com for 
#                   identifying the format in bootimg.h and 
#                   describing initial instructions for splitting
#                   the boot.img file.
#
#   Copyright (c) 2008 William Enck
#   Copyright (c) 2011 ox0spy
#
######################################################################

import os, sys
from struct import unpack

# Constants (from bootimg.h)
BOOT_MAGIC = 'ANDROID!'
BOOT_MAGIC_SIZE = 8
BOOT_NAME_SIZE = 16
BOOT_ARGS_SIZE = 512

# Unsigned integers are 4 bytes
UNSIGNED_SIZE = 4

# header_format (from bootimg.h)
'''struct boot_img_hdr
{
    unsigned char magic[BOOT_MAGIC_SIZE]

    unsigned kernel_size  /* size in bytes */
    unsigned kernel_addr  /* physical load addr */

    unsigned ramdisk_size /* size in bytes */
    unsigned ramdisk_addr /* physical load addr */

    unsigned second_size  /* size in bytes */
    unsigned second_addr  /* physical load addr */

    unsigned tags_addr    /* physical addr for kernel tags */
    unsigned page_size    /* flash page size we assume */
    unsigned unused[2]    /* future expansion: should be 0 */

    unsigned char name[BOOT_NAME_SIZE] /* asciiz product name */

    unsigned char cmdline[BOOT_ARGS_SIZE]

    unsigned id[8] /* timestamp / checksum / sha1 / etc */
}
'''

def parse_header(bootimg):
    fd = open(bootimg, 'r')

    # Read the Magic
    buf = fd.read(BOOT_MAGIC_SIZE)
    if buf != BOOT_MAGIC:
        print "Android Magic not found in $fn. Giving up."

    # Read kernel size and address (assume little-endian)
    buf = fd.read(UNSIGNED_SIZE * 2)
    (k_size, k_addr) = unpack("II", buf)

    # Read ramdisk size and address (assume little-endian)
    buf = fd.read(UNSIGNED_SIZE * 2)
    (r_size, r_addr) = unpack("II", buf)

    # Read second size and address (assume little-endian)
    buf = fd.read(UNSIGNED_SIZE * 2)
    (s_size, s_addr) = unpack("II", buf)

    # Ignore tags_addr
    fd.read(UNSIGNED_SIZE)

    # get the page size (assume little-endian)
    buf = fd.read(UNSIGNED_SIZE)
    p_size = unpack("I", buf)[0]

    # Ignore unused
    fd.read(UNSIGNED_SIZE * 2)

    # Read the name (board name)
    buf = fd.read(BOOT_NAME_SIZE)
    name = buf

    # Read the command line
    buf = fd.read(BOOT_ARGS_SIZE)
    cmdline = buf

    # Ignore the id
    fd.read(UNSIGNED_SIZE * 8)

    # Close the file
    fd.close()

    # Print important values
    print "Page size: \t%d (0x%x)" %(p_size, p_size)
    print "Kernel size: \t%d (0x%x)" %(k_size, k_size)
    print "Ramdisk size: \t%d (0x%x)" %(r_size, r_size)
    print "Second size: \t%d (0x%x)" %(s_size, s_size)
    print "Board name: \t%s" % name
    print "Command line: \t%s" % cmdline

    # page size, kernel size, ramdisk size, second size
    return (p_size, k_size, r_size, s_size)

# dump file from offset to (offset + size)
def dump_file(infile, outfile, offset, size):
    fin = open(infile, 'r')
    fout = open(outfile, 'w')

    fin.seek(offset, os.SEEK_CUR)
    data = fin.read(size)
    fout.write(data)

    fin.close()
    fout.close()

# display script usage
def usage():
    print 'Usage: %s boot.img\n' % sys.argv[0]

# format (from bootimg.h)
'''
** +-----------------+
** | boot header     | 1 page
** +-----------------+
** | kernel          | n pages
** +-----------------+
** | ramdisk         | m pages
** +-----------------+
** | second stage    | o pages
** +-----------------+
**
** n = (kernel_size + page_size - 1) / page_size
** m = (ramdisk_size + page_size - 1) / page_size
** o = (second_size + page_size - 1) / page_size
'''

# main
def main():
    if len(sys.argv) == 1:
        usage()
    
    bootimg = sys.argv[1]
    (p_size, k_size, r_size, s_size) = parse_header(bootimg)

    n = int((k_size + p_size - 1) / p_size)
    m = int((r_size + p_size - 1) / p_size)
    o = int((s_size + p_size - 1) / p_size)

    k_offset = p_size
    r_offset = k_offset + (n * p_size)
    s_offset = r_offset + (m * p_size)

    base = os.path.basename(bootimg).split('.')[0]
    k_file = base + "-kernel"
    r_file = base + "-ramdisk.gz"
    s_file = base + "-second.gz"

    # The kernel is always there
    print "Writing %s ..." % k_file,
    dump_file(bootimg, k_file, k_offset, k_size)
    print " complete."

    # The ramdisk is always there
    print "Writing %s ..." % r_file,
    dump_file(bootimg, r_file, r_offset, r_size)
    print " complete."

    # The Second stage bootloader is optional
    if s_size != 0:
        print "Writing %s ..." % s_file,
        dump_file(bootimg, s_file, s_offset, s_size)
        print " complete."

if __name__ == '__main__':
    main()
