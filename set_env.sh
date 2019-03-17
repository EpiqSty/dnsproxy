#!/bin/bash

source <(sed -E -n 's/[^#]+/export &/ p' ./.env)