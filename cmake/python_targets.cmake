find_program(PIP
        NAMES
            pip${Python3_VERSION_MAJOR}.${Python3_VERSION_MINOR}
            pip
        REQUIRED
        )

set(PIP_INDEX_URL https://devpi.library.illinois.edu/production/release CACHE STRING "URL used to find Python dependent packages")
if(PIP)
    execute_process(COMMAND ${PIP} wheel --help
            RESULT_VARIABLE PIP_WHEEL_FOUND
            OUTPUT_QUIET
            )
    if (PIP_WHEEL_FOUND EQUAL 0)
        add_custom_target(wheel
            COMMAND ${PIP} wheel -w ${PROJECT_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR} -i ${PIP_INDEX_URL}
        )
    else()
        message(WARNING "Requires wheel package to build wheels")
    endif()


endif()
