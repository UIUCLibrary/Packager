Feature: Transform package objects
  Scenario Outline: package containing 2 objects and want to transform them into a another type of package
    Given A package containing 2 objects of <source_package_type>
    And We have another path to save the objects to <new_package_type>
    When we transform all the packages found into the new <new_package_type> package format
    Then the newly transformed package should contain the same files but in the <new_package_type> format
    Examples:
      | source_package_type | new_package_type  |
      | CaptureOnePackage   | HathiTiff         |
      | HathiTiff           | CaptureOnePackage |

  Scenario: Capture One session with a .DS_Store file transform to a HathiTrust Tiff package
    Given A Capture One session package containing 2 objects and a .DS_Store file in it
    When we transform all the packages found into a HathiTiff Package
    Then The resulting package is a HathiTiff Package

  Scenario: Capture One session with a thumbs.db file transform to a HathiTrust Tiff package
    Given A Capture One session package containing 2 objects and a thumbs.db file in it
    When we transform all the packages found into a HathiTiff Package
    Then The resulting package is a HathiTiff Package
