@echo off
setlocal enabledelayedexpansion

:: Title
title CEASIOMpy Full Installation Script
echo ============================================
echo CEASIOMpy Full Installation Script for Windows
echo ============================================
echo.

:: Install Miniconda
echo Installing Miniconda...
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
start /wait Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /AddToPath=1 /RegisterPython=1 /S
del Miniconda3-latest-Windows-x86_64.exe
echo Miniconda installation complete.
echo.

:: Install CEASIOMpy
echo Installing CEASIOMpy...
call conda create -n ceasiompy python=3.8 -y
call conda activate ceasiompy
curl -O https://raw.githubusercontent.com/cfsengineering/CEASIOMpy/main/environment.yml
call mamba env update -n ceasiompy -f environment.yml
call pip install -e .
echo CEASIOMpy installation complete.
echo.

:: Install SU2
echo Installing SU2...
curl -O https://github.com/su2code/SU2/releases/download/v8.1.0/SU2-v8.1.0-win64-mpi.zip
mkdir SU2
tar -xf SU2-v8.1.0-win64-mpi.zip -C SU2
setx PATH "%cd%\SU2\bin;%PATH%"
echo SU2 installation complete.
echo.

:: Install MPICH
echo Installing MPICH...
curl -O https://www.mpich.org/static/downloads/4.3/mpich-4.3.0-win-x86-64.msi
msiexec /i mpich-4.3.0-win-x86-64.msi /quiet
setx PATH "%ProgramFiles%\MPICH2\bin;%PATH%"
echo MPICH installation complete.
echo.

:: Install Paraview
echo Installing Paraview...
curl -O https://www.paraview.org/files/v5.13/ParaView-5.13.3-MPI-Windows-Python3.10-msvc2017-AMD64.msi
mkdir Paraview
tar -xf ParaView-5.11.0-Windows-Python3.9-msvc2017-64bit.zip -C Paraview
setx PATH "%cd%\Paraview\bin;%PATH%"
echo Paraview installation complete.
echo.

:: Finish
echo ============================================
echo All components installed successfully.
echo ============================================
pause
exit