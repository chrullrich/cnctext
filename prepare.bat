@echo off

rem Prepares individual .cnc files from a multi-line input file,
rem one line per set of markers.
rem
rem The first argument to this script is the name of the input file.
rem All further arguments are passed to cnctext.
rem
rem File format:
rem 
rem ID;Line 1.1;Line 1.2;Line 2.1;Line 2.2
rem
rem ID is used in the name of the output file; the Lines are 
rem passed to cnctext.
rem
rem Single-line tags and --double are not supported.

@echo on
for /f "delims=; tokens=1-5" %%a in (%1) do cnctext -o tag%%a.cnc %2 %3 %4 %5 %6 %7 %8 %9 "%%b" "%%c" "%%d" "%%e"

