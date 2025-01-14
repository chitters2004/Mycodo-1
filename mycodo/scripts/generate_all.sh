#!/bin/bash
#
# Generates all required Mycodo files
#
# Includes:
#
# Manual versions (PDF, HTML, TXT)
# Translations

INSTALL_DIRECTORY=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd -P )

/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/generate_manual_pandoc.sh
/bin/bash ${INSTALL_DIRECTORY}/mycodo/scripts/generate_translations_pybabel.sh
