#!/bin/bash
fab package deploy build_newproject start_mech -u ubuntu -i ~/.ssh/load.pem -H $1
