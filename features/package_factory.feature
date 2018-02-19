# Created by hborcher at 2/2/2018
Feature: Build package objects
  # You should easily be able to build a new package object using the package factory

  Scenario: Capture One session containing 2 objects
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    Then resulting packages should be 2
    And the first Capture One object should contain everything from the first group
    And the second Capture One object should contain everything from the second group

  Scenario: Hathi TIFF package containing 2 objects
    Given We have hathi tiff package containing a folder made up of 2 objects
    When we create a HathiTiff object factory and use it to identify packages at the root folder
    Then resulting packages should be 2
    And the first Hathi TIFF object should contain everything from the first group
    And the second Hathi TIFF object should contain everything from the second group

  Scenario: Capture One session containing 2 objects and want to transform them into a HathiTrust Tiff package
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    And we transform all the packages found into Hathi tiff packages
    Then the newly transformed package should contain the same files but in the format for Hathi Trust

  Scenario: HathiTrust Tiff package containing 2 objects and want to transform them into a Capture One session
    Given We have hathi tiff package containing a folder made up of 2 objects
    When we create a HathiTiff object factory and use it to identify packages at the root folder
    And we transform all the packages found into Capture One packages
    Then the newly transformed package should contain the same files but in the format for Capture One

  Scenario: Capture One session containing 2 objects and want to transform them into a Digital Library Compound
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    And we transform all the packages found into Digital Library Compound Objects packages
    Then the newly transformed package should contain the same files but in the format for Digital Library Compound Objects

  Scenario: Digital Library Compound session containing 2 objects
    Given We have a folder contains two Digital Library Compound objects
    When we create a Digital Library Compound object factory and use it to identify packages at the root folder
    Then the resulting package should be a Digital Library Compound Object type
    And resulting packages should be 2
    And the first Digital Library Compound object should contain everything from the first group
    And the second Digital Library Compound object should contain everything from the second group


  Scenario: Capture One session containing 2 objects with system files and want to transform them into a HathiTrust Tiff package
    Given We have a flat folder contains files that belong to two groups, grouped by the number left of an underscore
    And the folder flat folder has a Thumbs.db file in it
    When we create a CaptureOne object factory and use it to identify packages at the root folder
    And we transform all the packages found into Hathi tiff packages
    Then the newly transformed package should contain the same files but in the format for Hathi Trust
