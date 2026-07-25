#!/bin/bash

echo -n "Welcome to USB format Program! "
echo "We need to become root!"

sudo fdisk -l

echo -n "Which drive do you want to format? "
read drive

sudo wipefs --all "$drive"

sudo cfdisk "$drive"

read -p "Enter the label for the filesystem: " name

sudo mkfs.vfat -n "$name" "$drive"

