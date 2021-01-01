cmake_minimum_required(VERSION 3.17)
project(uiucprescon.packager
        LANGUAGES NONE
        )

find_package(Python3 COMPONENTS Interpreter)

if(Python3_Interpreter_FOUND)
    include(cmake/python_targets.cmake)
endif()