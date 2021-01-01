cmake_minimum_required(VERSION 3.17)
project(uiucprescon.packager
        LANGUAGES NONE
        )

find_package(Python3 COMPONENTS Interpreter)

if(Python3_Interpreter_FOUND)
    include(cmake/python_targets.cmake)
endif()

if(UNIX)
    #   This needs the bind the docker socket to work which doesn't work on Windows to
    #   my as far as I know
    if(${PROJECT_NAME}_TESTCI)
        include(cmake/jenkins.cmake)
    endif()
endif()