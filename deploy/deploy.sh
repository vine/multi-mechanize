#!/bin/bash
fab package deploy -x leigh -i ~/.ssh/id_rsa -H load01.stg.vine.co
