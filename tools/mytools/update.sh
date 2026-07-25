#!/usr/bin/bash

sudo apt update
sudo apt list --upgradable
sudo parrot-upgrade
sudo apt autoremove