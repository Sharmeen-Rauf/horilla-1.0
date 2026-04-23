@echo off
REM Run Django dev server with env vars that reduce OpenBLAS memory use (avoids crash on some Windows systems)
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
set MKL_NUM_THREADS=1
set NUMEXPR_MAX_THREADS=1
python manage.py runserver %*
