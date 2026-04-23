#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings

# Reduce OpenBLAS/NumPy memory use on Windows to avoid "Memory allocation still failed"
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_MAX_THREADS"):
    os.environ[key] = "1"

# Suppress requests dependency version warning (urllib3/chardet/charset_normalizer)
warnings.filterwarnings("ignore", message=".*doesn't match a supported version.*")


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "horilla.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
