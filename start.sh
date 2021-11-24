#!/bin/bash
systemctl  daemon-reload
set Password tublood
send "$Password\r"
set user tublood
systemctl start  auto_trade.service
set Password tublood
